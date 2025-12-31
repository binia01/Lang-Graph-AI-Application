# AI Career & Learning Coach

This application is an AI-powered Career and Learning Coach built using **LangGraph**. It helps users analyze their career goals, identify skill gaps, and generates a personalized learning plan. It features a Human-in-the-Loop (HITL) workflow, allowing users to review and refine the plan before finalizing it.

## Features

-   **Profile Analysis**: Extracts career goals and current skills from user input.
-   **Gap Analysis**: Identifies missing skills required for the target career.
-   **Plan Generation**: Creates a detailed learning plan with resources and timelines.
-   **Human-in-the-Loop**: Pauses for user review. Users can approve the plan or request changes.
-   **Iterative Refinement**: The AI refines the plan based on user feedback.
-   **Persistence**: Saves the conversation state using SQLite, allowing for long-running sessions.

## Project Structure

-   `app.py`: Streamlit web application (UI).
-   `main.py`: Command-line interface (CLI).
-   `src/graph.py`: Defines the LangGraph workflow (nodes and edges).
-   `src/nodes.py`: Implements the logic for each node (LLM calls).
-   `src/state.py`: Defines the state schema.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    Create a `.env` file in the root directory and add your Google API Key (or OpenAI if you modify the code):
    ```
    GOOGLE_API_KEY=your_api_key_here
    ```

## Running the Application

### Web UI (Streamlit)
```bash
streamlit run app.py
```

### CLI
```bash
python main.py
```

## Workflow Logic

1.  **Start**: User inputs goals and skills.
2.  **Profile Analyzer**: AI structures the input.
3.  **Gap Analyzer**: AI compares skills to market needs.
4.  **Plan Generator**: AI creates a learning plan.
5.  **Human Review (Interrupt)**: The system pauses.
    -   User reviews the plan.
    -   User provides feedback ("Approve" or "Change X").
6.  **Decision**:
    -   If **Approved**: Workflow ends.
    -   If **Rejected**: Workflow goes to **Plan Refiner**.
7.  **Plan Refiner**: AI updates the plan based on feedback and loops back to **Human Review**.
