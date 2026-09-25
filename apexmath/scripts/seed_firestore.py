"""Seed Firestore with initial practice problems and curriculum for ApexMath."""

from google.cloud import firestore

# CRITICAL: Hardcode the GCP Project ID as a string.
# Do not read from google.auth.default() or GOOGLE_CLOUD_PROJECT,
# which can return the project number in Agent Platform environments.
PROJECT_ID = "qwiklabs-gcp-04-47563a3307b3"
COLLECTION_PROBLEMS = "practice_problems"

SEED_PROBLEMS = [
    {
        "id": "calc-limit-lhopital",
        "title": "Indeterminate Limits via L'Hôpital's Rule",
        "course": "AP Calculus AB/BC",
        "topic": "Limits & Continuity",
        "subtopic": "L'Hôpital's Rule",
        "difficulty": "medium",
        "question": "Evaluate the limit: lim_{x -> 0} (e^(2x) - 1) / sin(3x)",
        "hints": [
            "Test direct substitution: notice the numerator is e^0 - 1 = 0 and denominator is sin(0) = 0.",
            "Since it is indeterminate form 0/0, apply L'Hôpital's Rule: differentiate numerator and denominator separately with respect to x.",
        ],
        "final_answer": "2/3",
        "step_by_step_solution": (
            "1. Check indeterminate form: (e^0 - 1)/sin(0) = 0/0.\n"
            "2. Apply L'Hôpital's Rule by differentiating top and bottom:\n"
            "   d/dx[e^(2x) - 1] = 2*e^(2x)\n"
            "   d/dx[sin(3x)] = 3*cos(3x)\n"
            "3. Evaluate the new limit as x -> 0:\n"
            "   (2*e^0) / (3*cos(0)) = (2*1) / (3*1) = 2/3."
        ),
        "ap_exam_tips": "On AP Free Response questions, you must explicitly state that the limit is of indeterminate form (0/0) before applying L'Hôpital's Rule, or you will lose points.",
    },
    {
        "id": "calc-derivative-chain-rule",
        "title": "Differentiating Logarithmic Functions with Chain Rule",
        "course": "AP Calculus AB/BC",
        "topic": "Differentiation",
        "subtopic": "Chain Rule",
        "difficulty": "easy",
        "question": "Find the derivative of f(x) = ln(x^2 + 4) with respect to x.",
        "hints": [
            "Recall the derivative of ln(u) with respect to x is (1/u) * u'.",
            "Here, inner function u = x^2 + 4. What is u'?",
        ],
        "final_answer": "2x / (x^2 + 4)",
        "step_by_step_solution": (
            "1. Let u = x^2 + 4, so f(u) = ln(u).\n"
            "2. By Chain Rule: f'(x) = (1/u) * (du/dx).\n"
            "3. Compute du/dx: d/dx[x^2 + 4] = 2x.\n"
            "4. Combine: f'(x) = (1/(x^2 + 4)) * 2x = 2x / (x^2 + 4)."
        ),
        "ap_exam_tips": "Keep the denominator factored or as (x^2 + 4); do not try to expand or divide terms incorrectly.",
    },
    {
        "id": "calc-integral-substitution",
        "title": "Definite Integration via U-Substitution",
        "course": "AP Calculus AB/BC",
        "topic": "Integration",
        "subtopic": "U-Substitution",
        "difficulty": "medium",
        "question": "Evaluate the indefinite integral: integral 2x * cos(x^2) dx",
        "hints": [
            "Look for a function and its derivative: notice x^2 inside cos() and 2x outside.",
            "Choose u = x^2. What is du?",
        ],
        "final_answer": "sin(x^2) + C",
        "step_by_step_solution": (
            "1. Let u = x^2.\n"
            "2. Differentiate: du = 2x dx.\n"
            "3. Substitute into the integral: integral cos(u) du.\n"
            "4. Integrate with respect to u: sin(u) + C.\n"
            "5. Back-substitute u = x^2: sin(x^2) + C."
        ),
        "ap_exam_tips": "Never forget '+ C' for indefinite integrals on the AP exam!",
    },
    {
        "id": "precalc-trig-equation",
        "title": "Solving Trigonometric Equations with Double Angle Identity",
        "course": "Pre-Calculus",
        "topic": "Trigonometry",
        "subtopic": "Double Angle Identities",
        "difficulty": "hard",
        "question": "Find all exact solutions for theta in [0, 2*pi) that satisfy: sin(2*theta) = cos(theta)",
        "hints": [
            "Use the double-angle identity for sine: sin(2*theta) = 2*sin(theta)*cos(theta).",
            "Move all terms to one side: 2*sin(theta)*cos(theta) - cos(theta) = 0 and factor out cos(theta).",
        ],
        "final_answer": "pi/6, pi/2, 5pi/6, 3pi/2",
        "step_by_step_solution": (
            "1. Apply identity: 2*sin(theta)*cos(theta) = cos(theta).\n"
            "2. Subtract cos(theta) from both sides: 2*sin(theta)*cos(theta) - cos(theta) = 0.\n"
            "3. Factor out cos(theta): cos(theta) * (2*sin(theta) - 1) = 0.\n"
            "4. Case 1: cos(theta) = 0 => theta = pi/2, 3pi/2 in [0, 2*pi).\n"
            "5. Case 2: 2*sin(theta) - 1 = 0 => sin(theta) = 1/2 => theta = pi/6, 5pi/6.\n"
            "6. All solutions in [0, 2*pi): pi/6, pi/2, 5pi/6, 3pi/2."
        ),
        "ap_exam_tips": "Do NOT divide both sides by cos(theta) at the start, or you will lose the solutions where cos(theta) = 0!",
    },
]


def seed():
    print(f"Connecting to Firestore for project: '{PROJECT_ID}'...")
    db = firestore.Client(project=PROJECT_ID)
    collection = db.collection(COLLECTION_PROBLEMS)

    for item in SEED_PROBLEMS:
        doc_id = item["id"]
        doc_data = {k: v for k, v in item.items() if k != "id"}
        collection.document(doc_id).set(doc_data)
        print(f"✓ Seeded problem: '{item['title']}' (id: {doc_id})")

    print(
        f"\nSuccessfully seeded {len(SEED_PROBLEMS)} practice problems in '{COLLECTION_PROBLEMS}'."
    )


if __name__ == "__main__":
    seed()
