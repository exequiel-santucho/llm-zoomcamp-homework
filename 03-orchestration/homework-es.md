## Homework: AI Orchestration with Kestra

ATTENTION: At the end of the submission form, you will be required to include a link to your GitHub repository or other public code-hosting site. This repository should contain your code for solving the homework. If your solution includes code that is not in file format, please include these directly in the README file of your repository.

> It's possible your answers won't match exactly. If so, select the closest one

## Prerequisites

Before starting this homework, ensure you have:

1. Completed the [Module 3 lessons](../../../03-orchestration/README.md) — the questions reference flows and concepts covered there
2. Kestra running locally with API keys configured (see the [Setup](../../../03-orchestration/lessons/03-setup.md) lesson) -- this includes the Gemini API key, which is also required for the AI Copilot
3. Imported all flows from the `03-orchestration/flows/` directory (covered in the Setup lesson)

## Question 1: Context Engineering

Try the following experiment:

1. Open ChatGPT in a private browser window: https://chatgpt.com
2. Enter this prompt: "Create a Kestra flow that loads NYC taxi data from CSV to BigQuery"
3. Then, use Kestra's AI Copilot with the same prompt

After trying the same prompt in ChatGPT vs Kestra's AI Copilot, what is the primary reason AI Copilot generates better Kestra flows?

- AI Copilot uses a more powerful model
- **AI Copilot has access to current Kestra plugin documentation** ✓
- AI Copilot uses more tokens
- AI Copilot has internet access

**Respuesta:** AI Copilot has access to current Kestra plugin documentation. ChatGPT solo conoce lo que vio en su entrenamiento, mientras que el AI Copilot de Kestra tiene acceso a la documentación actualizada de los plugins, lo que le permite generar YAML válido y con la sintaxis correcta.

## Question 2: RAG vs No RAG

Run both `1_chat_without_rag.yaml` and `2_chat_with_rag.yaml` in the Kestra UI. Read the execution logs for each.

The non-RAG response about Kestra 1.1 features is best described as:

- Accurate and specific, matching the actual release notes
- **Vague, generic, or fabricated — the model guesses from training data** ✓
- Empty — the model refuses to answer without context
- Identical to the RAG version

**Respuesta:** Vague, generic, or fabricated. Al ejecutar `1_chat_without_rag.yaml`, el modelo (Gemini) inventó features plausibles pero incorrectas (ej: "New Topology View", "Flow Variables and Expressions Preview", "Namespace-level Secrets and Variables") que no coinciden con el release real. Al ejecutar `2_chat_with_rag.yaml`, que ingesta la nota de lanzamiento real, la respuesta coincidió exactamente con las features reales (Redesigned UI Filters, No-Code Dashboard Editor, Human-in-the-Loop, Multi-Agent AI Systems, Fix with AI).

## Question 3: Token usage — short summary

Run `4_simple_agent.yaml` with `summary_length = short` (leave the other inputs as defaults).

Open the execution logs and find the token usage logged by the `log_token_usage` task.

What is the approximate **output** token count for `multilingual_agent`?

- 5-15 tokens
- **60-100 tokens** ✓
- 200-400 tokens
- 500+ tokens

**Respuesta:** 60-100 tokens (valor real obtenido: 57 output tokens para `multilingual_agent` con `summary_length=short`)

## Question 4: Token usage — long summary

Run `4_simple_agent.yaml` again with `summary_length = long`.

Compare the `multilingual_agent` output token count to your result from Question 3. Roughly how many times more output tokens does the long summary use?

- About the same (within 20%)
- **2-5x more** ✓
- 10-20x more
- 50x more

**Respuesta:** 2-5x more (valor real: 57 tokens con `short` → 194 tokens con `long`, un factor de ~3.4x)

## Question 5: Modifying a flow

Open `4_simple_agent.yaml` in the Kestra flow editor. Find the `english_brevity` task and change its prompt from asking for exactly **1 sentence** to asking for exactly **3 sentences**.

Save the flow, then run it with `summary_length = long`.

Compare the `english_brevity` output token count to the original 1-sentence version (also with `summary_length = long`). How do they compare?

- About the same (within 20%)
- **2-4x more** ✓
- 5-10x more
- 10x+ more

**Respuesta:** 2-4x more (valor real: 36 tokens con "exactly 1 sentence" → 83 tokens con "exactly 3 sentences", un factor de ~2.3x)

## Question 6: Best Practices

Based on what you learned in this module, for production workflows requiring deterministic, repeatable results with strict compliance requirements (e.g., financial reporting, workflows in highly regulated industries), which approach is most appropriate?

- Always use AI agents for maximum flexibility and adaptation
- **Use traditional task-based workflows for predictability and auditability** ✓
- Use only RAG without agents for better performance
- Use web search tools exclusively to ensure current data

**Respuesta:** Use traditional task-based workflows for predictability and auditability. Los agentes de IA son flexibles pero no determinísticos (el modelo puede variar sus decisiones entre ejecuciones), lo cual es inaceptable en reportes financieros o industrias reguladas donde se requiere auditabilidad y resultados reproducibles.

## Learning in Public

We encourage everyone to share what they learned. This is called "learning in public".

Read more about the benefits [here](https://alexeyondata.substack.com/p/benefits-of-learning-in-public-and) and in the [course's learning in public guide](https://datatalks.club/docs/courses/zoomcamp-logistics/learning-in-public/).

## Submitting the Solutions

* Form for submitting: https://courses.datatalks.club/llm-zoomcamp-2026/homework/hw3
* Check the link above to see the due date
