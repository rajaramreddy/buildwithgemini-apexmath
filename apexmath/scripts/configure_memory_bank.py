"""Configures Vertex AI Memory Bank topics and few-shot examples for ApexMath.

Ensures that user questions, exercises, scores, errors, and weak concepts
are tracked and extracted into long-term memory across sessions.
"""

from agentplatform import Client
from agentplatform._genai import types
from google.genai import types as genai_types

PROJECT_ID = "qwiklabs-gcp-04-47563a3307b3"
LOCATION = "us-east1"
AGENT_ENGINE_ID = "7022297092605345792"
ENGINE_RESOURCE_NAME = (
    f"projects/210430842247/locations/{LOCATION}/reasoningEngines/{AGENT_ENGINE_ID}"
)


def configure_memory_bank() -> None:
    client = Client(project=PROJECT_ID, location=LOCATION)

    example_question = types.MemoryBankCustomizationConfigGenerateMemoriesExample(
        conversation_source=types.MemoryBankCustomizationConfigGenerateMemoriesExampleConversationSource(
            events=[
                types.MemoryBankCustomizationConfigGenerateMemoriesExampleConversationSourceEvent(
                    content=genai_types.Content(
                        role="user",
                        parts=[
                            genai_types.Part.from_text(
                                text="Can you explain how the chain rule works when differentiating composite functions like sin(x^2)?"
                            )
                        ],
                    )
                ),
                types.MemoryBankCustomizationConfigGenerateMemoriesExampleConversationSourceEvent(
                    content=genai_types.Content(
                        role="model",
                        parts=[
                            genai_types.Part.from_text(
                                text="The chain rule states d/dx[f(g(x))] = f'(g(x)) * g'(x). For sin(x^2), the outer function is sin(u) and inner is u=x^2, giving cos(x^2) * 2x."
                            )
                        ],
                    )
                ),
            ]
        ),
        generated_memories=[
            types.MemoryBankCustomizationConfigGenerateMemoriesExampleGeneratedMemory(
                fact="The student asked for an explanation of how the chain rule applies to composite functions like sin(x^2)."
            )
        ],
    )

    example_exercise = types.MemoryBankCustomizationConfigGenerateMemoriesExample(
        conversation_source=types.MemoryBankCustomizationConfigGenerateMemoriesExampleConversationSource(
            events=[
                types.MemoryBankCustomizationConfigGenerateMemoriesExampleConversationSourceEvent(
                    content=genai_types.Content(
                        role="model",
                        parts=[
                            genai_types.Part.from_text(
                                text="Let us try this AP Calculus AB problem: Find the derivative of f(x) = ln(3x^2 + 1)."
                            )
                        ],
                    )
                ),
                types.MemoryBankCustomizationConfigGenerateMemoriesExampleConversationSourceEvent(
                    content=genai_types.Content(
                        role="user",
                        parts=[
                            genai_types.Part.from_text(
                                text="I think it is 1 / (3x^2 + 1)."
                            )
                        ],
                    )
                ),
                types.MemoryBankCustomizationConfigGenerateMemoriesExampleConversationSourceEvent(
                    content=genai_types.Content(
                        role="model",
                        parts=[
                            genai_types.Part.from_text(
                                text="Almost! Your score is 0/1. You correctly identified 1/u, but forgot to multiply by the derivative of the inside du/dx = 6x, so the correct derivative is 6x / (3x^2 + 1)."
                            )
                        ],
                    )
                ),
            ]
        ),
        generated_memories=[
            types.MemoryBankCustomizationConfigGenerateMemoriesExampleGeneratedMemory(
                fact="The student attempted exercise derivative of ln(3x^2 + 1) and scored 0/1, mistakenly omitting the chain rule factor 6x and answering 1/(3x^2+1)."
            ),
            types.MemoryBankCustomizationConfigGenerateMemoriesExampleGeneratedMemory(
                fact="The student needs targeted review on applying the chain rule to logarithmic functions."
            ),
        ],
    )

    custom_config = types.MemoryBankCustomizationConfig(
        memory_topics=[
            types.MemoryBankCustomizationConfigMemoryTopic(
                managed_memory_topic=types.MemoryBankCustomizationConfigMemoryTopicManagedMemoryTopic(
                    managed_topic_enum="USER_PERSONAL_INFO"
                )
            ),
            types.MemoryBankCustomizationConfigMemoryTopic(
                managed_memory_topic=types.MemoryBankCustomizationConfigMemoryTopicManagedMemoryTopic(
                    managed_topic_enum="USER_PREFERENCES"
                )
            ),
            types.MemoryBankCustomizationConfigMemoryTopic(
                managed_memory_topic=types.MemoryBankCustomizationConfigMemoryTopicManagedMemoryTopic(
                    managed_topic_enum="KEY_CONVERSATION_DETAILS"
                )
            ),
            types.MemoryBankCustomizationConfigMemoryTopic(
                managed_memory_topic=types.MemoryBankCustomizationConfigMemoryTopicManagedMemoryTopic(
                    managed_topic_enum="EXPLICIT_INSTRUCTIONS"
                )
            ),
            types.MemoryBankCustomizationConfigMemoryTopic(
                custom_memory_topic=types.MemoryBankCustomizationConfigMemoryTopicCustomMemoryTopic(
                    label="user_questions_and_inquiries",
                    description=(
                        "All questions, inquiries, and mathematical topics asked by the student during sessions, "
                        "capturing concepts they want to understand or need clarification on."
                    ),
                )
            ),
            types.MemoryBankCustomizationConfigMemoryTopic(
                custom_memory_topic=types.MemoryBankCustomizationConfigMemoryTopicCustomMemoryTopic(
                    label="exercise_scores_and_mistakes",
                    description=(
                        "Practice exercises and problems attempted by the student, their scores, specific errors or misconceptions made, "
                        "and weak concepts that need targeted reinforcement and additional exercises."
                    ),
                )
            ),
        ],
        generate_memories_examples=[example_question, example_exercise],
    )

    context_spec = types.ReasoningEngineContextSpec(
        memory_bank_config=types.ReasoningEngineContextSpecMemoryBankConfig(
            customization_configs=[custom_config]
        )
    )

    print(f"Updating Memory Bank on {ENGINE_RESOURCE_NAME}...")
    updated = client.agent_engines.update(
        name=ENGINE_RESOURCE_NAME,
        config=types.AgentEngineConfig(context_spec=context_spec),
    )
    print("Memory Bank configured successfully!")
    return updated


if __name__ == "__main__":
    configure_memory_bank()
