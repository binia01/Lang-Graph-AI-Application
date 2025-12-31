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
The recommended way to use the Coach is via the web interface.
```bash
streamlit run app.py
```

### CLI
For testing the core logic without a UI:
```bash
python main.py
```

## User Guide

### 1. Starting a Session
- Launch the Streamlit app.
- You will see a chat interface.
- **New Session**: Click "New Session" in the sidebar to start a fresh coaching thread.
- **History**: Previous sessions are listed in the sidebar. Click one to resume.

### 2. The Coaching Process
1.  **Profile Input**: The Coach will ask for your career goals and current skills. Enter them in the chat input.
2.  **Analysis**: The AI will analyze your profile and identify skill gaps.
3.  **Plan Generation**: A draft learning plan will be generated and displayed.

### 3. Human-in-the-Loop (Review & Feedback)
Once the plan is generated, the workflow pauses for your input. You have two options:
-   **Approve**: Type "approve" to finalize the plan. The workflow will complete.
-   **Request Changes**: Type your feedback (e.g., "I want to focus more on Python" or "Remove the certification requirement").
    -   The AI will refine the plan based on your feedback and present it again for review.

### 4. Viewing Results
-   The conversation history is preserved.
-   You can scroll up to see previous versions of the plan and the analysis.

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
