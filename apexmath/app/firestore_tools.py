"""Firestore tools for ApexMath: AP Calculus and Pre-Calculus tutor."""

import datetime
import json

from google.cloud import firestore

# CRITICAL: Hardcode GCP Project ID as a string.
# Do not read from google.auth.default() or GOOGLE_CLOUD_PROJECT,
# which can return the project number in Agent Platform environments.
PROJECT_ID = "qwiklabs-gcp-04-47563a3307b3"
COLLECTION_PROBLEMS = "practice_problems"
COLLECTION_PROGRESS = "student_progress"

_db = None


def get_firestore_client() -> firestore.Client:
    """Lazy initialize Firestore client with hardcoded project ID."""
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID)
    return _db


def get_practice_problems(
    topic: str = "", difficulty: str = "", course: str = ""
) -> str:
    """Search and retrieve practice problems from the curriculum problem bank.

    Args:
        topic: Optional topic filter (e.g. 'Limits & Continuity', 'Differentiation', 'Integration', 'Trigonometry').
        difficulty: Optional difficulty ('easy', 'medium', 'hard').
        course: Optional course filter ('AP Calculus AB/BC', 'Pre-Calculus').

    Returns:
        JSON string containing matching problem cards with problem statements (solutions omitted).
    """
    db = get_firestore_client()
    docs = db.collection(COLLECTION_PROBLEMS).stream()

    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id

        if topic and topic.lower() not in data.get("topic", "").lower():
            continue

        if difficulty and difficulty.lower() != data.get("difficulty", "").lower():
            continue

        if course and course.lower() not in data.get("course", "").lower():
            continue

        results.append(
            {
                "id": data["id"],
                "title": data.get("title", ""),
                "course": data.get("course", ""),
                "topic": data.get("topic", ""),
                "subtopic": data.get("subtopic", ""),
                "difficulty": data.get("difficulty", ""),
                "question": data.get("question", ""),
                "hints_available": len(data.get("hints", [])),
            }
        )

    if not results:
        return json.dumps(
            {
                "message": "No practice problems found matching criteria.",
                "filters": {
                    "topic": topic or None,
                    "difficulty": difficulty or None,
                    "course": course or None,
                },
                "count": 0,
            }
        )

    return json.dumps({"count": len(results), "problems": results}, indent=2)


def get_problem_details(problem_id: str, view_mode: str = "hint") -> str:
    """Fetch hints or the complete step-by-step solution for a problem.

    Args:
        problem_id: The ID of the problem (e.g. 'calc-limit-lhopital', 'calc-derivative-chain-rule').
        view_mode: Either 'hint' (returns helpful hints without full solution),
                   'solution' (returns full step-by-step breakdown and final answer),
                   or 'all' (returns all details including AP tips).

    Returns:
        JSON string containing the requested hints or full solution.
    """
    db = get_firestore_client()
    doc_ref = db.collection(COLLECTION_PROBLEMS).document(problem_id)
    doc = doc_ref.get()

    if not doc.exists:
        # Fallback: search by partial title match
        for d in db.collection(COLLECTION_PROBLEMS).stream():
            if (
                problem_id.lower() in d.id.lower()
                or problem_id.lower() in d.to_dict().get("title", "").lower()
            ):
                doc = d
                break

    if not doc.exists:
        return json.dumps({"error": f"Practice problem '{problem_id}' not found."})

    data = doc.to_dict()
    data["id"] = doc.id

    if view_mode == "hint":
        return json.dumps(
            {
                "id": data["id"],
                "title": data.get("title", ""),
                "question": data.get("question", ""),
                "hints": data.get("hints", []),
            },
            indent=2,
        )

    if view_mode == "solution":
        return json.dumps(
            {
                "id": data["id"],
                "title": data.get("title", ""),
                "final_answer": data.get("final_answer", ""),
                "step_by_step_solution": data.get("step_by_step_solution", ""),
                "ap_exam_tips": data.get("ap_exam_tips", ""),
            },
            indent=2,
        )

    return json.dumps(data, indent=2)


def record_student_attempt(
    problem_id: str,
    student_answer: str,
    is_correct: bool,
    feedback: str,
    student_id: str = "student_user",
) -> str:
    """Log a student's problem attempt, correctness, and coaching feedback to track mastery.

    Args:
        problem_id: The problem ID attempted.
        student_answer: The answer provided by the student.
        is_correct: Whether the student's solution was correct.
        feedback: Personalized pedagogical feedback or conceptual advice for the student.
        student_id: Unique identifier for the student.

    Returns:
        JSON confirmation with attempt record details.
    """
    db = get_firestore_client()
    timestamp = datetime.datetime.now(datetime.UTC).isoformat()
    record = {
        "student_id": student_id,
        "problem_id": problem_id,
        "student_answer": student_answer,
        "is_correct": is_correct,
        "feedback": feedback,
        "timestamp": timestamp,
    }

    # Save to student_progress collection
    doc_ref = db.collection(COLLECTION_PROGRESS).document()
    doc_ref.set(record)
    record["id"] = doc_ref.id

    return json.dumps(
        {
            "status": "success",
            "message": f"Recorded attempt for problem '{problem_id}'.",
            "record": record,
        },
        indent=2,
    )


def add_practice_problem(
    title: str,
    course: str,
    topic: str,
    subtopic: str,
    difficulty: str,
    question: str,
    hints: list[str],
    final_answer: str,
    step_by_step_solution: str,
    ap_exam_tips: str,
) -> str:
    """Add a new practice problem to the Firestore problem bank.

    Args:
        title: Title of the problem.
        course: Course name ('AP Calculus AB', 'AP Calculus BC', 'Pre-Calculus').
        topic: Main topic area (e.g. 'Limits & Continuity', 'Differentiation', 'Integration', 'Series').
        subtopic: Specific technique (e.g. 'L\'Hôpital\'s Rule', 'Integration by Parts').
        difficulty: Difficulty level ('easy', 'medium', 'hard').
        question: The mathematical problem statement.
        hints: List of helpful guiding hints.
        final_answer: The final simplified mathematical answer.
        step_by_step_solution: Complete pedagogical solution.
        ap_exam_tips: Specific scoring tips or common student mistakes on AP exams.

    Returns:
        JSON confirmation with the created problem ID.
    """
    db = get_firestore_client()
    slug = title.lower().replace(" ", "-").replace("'", "").replace('"', "")[:30]
    doc_ref = db.collection(COLLECTION_PROBLEMS).document(slug)

    payload = {
        "title": title,
        "course": course,
        "topic": topic,
        "subtopic": subtopic,
        "difficulty": difficulty,
        "question": question,
        "hints": hints,
        "final_answer": final_answer,
        "step_by_step_solution": step_by_step_solution,
        "ap_exam_tips": ap_exam_tips,
    }

    doc_ref.set(payload)
    return json.dumps(
        {
            "status": "success",
            "message": f"Practice problem '{title}' added to bank.",
            "id": slug,
        },
        indent=2,
    )


def get_student_scorecard(student_id: str = "student_user") -> str:
    """Retrieve a summary scorecard of student progress, accuracy by topic, and recommended focus areas.

    Args:
        student_id: The ID of the student (default: 'student_user').

    Returns:
        JSON string containing total attempts, accuracy percentage, per-topic breakdown,
        and recommended review areas.
    """
    db = get_firestore_client()

    attempts_query = (
        db.collection(COLLECTION_PROGRESS)
        .where("student_id", "==", student_id)
        .stream()
    )
    attempts = [d.to_dict() for d in attempts_query]

    if not attempts:
        return json.dumps(
            {
                "student_id": student_id,
                "total_attempts": 0,
                "message": "No recorded practice attempts found yet. Try completing a problem first!",
                "recommended_focus": [
                    "Limits & Continuity",
                    "Differentiation",
                    "Integration",
                ],
            }
        )

    problem_topics = {}
    problems = db.collection(COLLECTION_PROBLEMS).stream()
    for p in problems:
        p_data = p.to_dict()
        problem_topics[p.id] = p_data.get("topic", "General")

    topic_stats: dict[str, dict[str, int]] = {}
    correct_count = 0

    for att in attempts:
        p_id = att.get("problem_id", "")
        topic = problem_topics.get(p_id, att.get("topic", "General"))
        if topic not in topic_stats:
            topic_stats[topic] = {"attempts": 0, "correct": 0}

        topic_stats[topic]["attempts"] += 1
        if att.get("is_correct", False):
            topic_stats[topic]["correct"] += 1
            correct_count += 1

    breakdown = {}
    weak_topics = []
    for topic, stats in topic_stats.items():
        accuracy = (
            round((stats["correct"] / stats["attempts"]) * 100, 1)
            if stats["attempts"]
            else 0.0
        )
        breakdown[topic] = {
            "attempts": stats["attempts"],
            "correct": stats["correct"],
            "accuracy_percent": accuracy,
        }
        if accuracy < 70.0:
            weak_topics.append(topic)

    total_attempts = len(attempts)
    overall_accuracy = (
        round((correct_count / total_attempts) * 100, 1) if total_attempts else 0.0
    )

    return json.dumps(
        {
            "student_id": student_id,
            "total_attempts": total_attempts,
            "correct_attempts": correct_count,
            "overall_accuracy_percent": overall_accuracy,
            "topic_breakdown": breakdown,
            "weak_topics_to_focus": weak_topics
            or ["All attempted topics have >= 70% accuracy. Keep up the great work!"],
        },
        indent=2,
    )
