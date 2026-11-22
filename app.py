import streamlit as st
import pandas as pd
import plotly.express as px
import hashlib
from datetime import datetime

from database import (
    create_database,
    get_table_schema,
    get_table_preview,
    get_schema_text,
    execute_query
)

from cloud_agent import build_agent, run_agent


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Chat With Your CSV | AI Data Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

if "agent_sql" not in st.session_state:
    st.session_state.agent_sql = None

if "agent_result" not in st.session_state:
    st.session_state.agent_result = None

if "agent_error" not in st.session_state:
    st.session_state.agent_error = None

if "manual_result" not in st.session_state:
    st.session_state.manual_result = None

if "query_history" not in st.session_state:
    st.session_state.query_history = []


# --------------------------------------------------
# THEME SELECTION
# --------------------------------------------------

with st.sidebar:
    st.markdown("## ✦ CSV Assistant")
    st.caption("AI-powered data exploration")

    st.divider()

    st.markdown("### Appearance")

    theme = st.selectbox(
        "Choose your theme",
        ["Dark", "Light"],
        index=0 if st.session_state.theme == "Dark" else 1
    )

    st.session_state.theme = theme

    st.divider()

    st.markdown("### Navigation")

    page = st.radio(
        "Go to",
        ["Overview", "AI Workspace", "Dataset Explorer"],
        label_visibility="collapsed"
    )

    st.divider()

    st.markdown("### Model Information")
    st.markdown("**LLM:** Qwen2.5-Coder-1.5B")
    st.markdown("**Agent:** LangGraph")
    st.markdown("**Database:** SQLite")
    st.markdown("**SQL Validator:** SQLGlot")

    st.divider()

    st.caption("Chat With Your CSV")
    st.caption("AI Data Assistant | 2026")


# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

if theme == "Dark":

    bg = "#0B1020"
    sidebar_bg = "#10172A"
    card_bg = "#151E33"
    text_color = "#E8ECF7"
    muted = "#9AA8C1"
    border_color = "#27334D"
    accent = "#9B7BFF"
    input_bg = "#151E33"

else:

    bg = "#F4F6FC"
    sidebar_bg = "#FFFFFF"
    card_bg = "#FFFFFF"
    text_color = "#182238"
    muted = "#68758C"
    border_color = "#E1E6F0"
    accent = "#7048E8"
    input_bg = "#FFFFFF"


st.markdown(
    f"""
    <style>

    .stApp {{
        background-color: {bg};
        color: {text_color};
    }}

    [data-testid="stSidebar"] {{
        background-color: {sidebar_bg};
        border-right: 1px solid {border_color};
    }}

    [data-testid="stHeader"] {{
        background-color: transparent;
    }}

    .block-container {{
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1450px;
    }}

    h1, h2, h3, h4, p, label, span {{
        color: {text_color};
    }}

    .hero {{
        background: linear-gradient(
            120deg,
            #28204C,
            #192D57,
            #17213B
        );
        padding: 30px;
        border-radius: 18px;
        margin-bottom: 25px;
        border: 1px solid #51417D;
    }}

    .hero h1 {{
        color: #FFFFFF !important;
        font-size: 32px;
        margin-bottom: 8px;
    }}

    .hero p {{
        color: #C6CBE2 !important;
        font-size: 15px;
        margin-bottom: 0;
    }}

    .section-label {{
        color: {accent} !important;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
    }}

    [data-testid="stMetric"] {{
        background-color: {card_bg};
        border: 1px solid {border_color};
        border-radius: 14px;
        padding: 20px;
    }}

    [data-testid="stMetricLabel"] {{
        color: {muted} !important;
    }}

    [data-testid="stMetricValue"] {{
        color: {text_color} !important;
    }}

    [data-testid="stDataFrame"] {{
        border: 1px solid {border_color};
        border-radius: 12px;
        overflow: hidden;
    }}

    .stTextInput input,
    .stTextArea textarea {{
        background-color: {input_bg};
        color: {text_color};
        border: 1px solid {border_color};
        border-radius: 10px;
    }}

    .stSelectbox div[data-baseweb="select"] > div {{
        background-color: {input_bg};
        border-color: {border_color};
    }}

    .stButton button,
    .stFormSubmitButton button {{
        background: linear-gradient(100deg, #7652E8, #3978E8);
        color: white !important;
        border: none;
        border-radius: 10px;
        padding: 8px 20px;
        font-weight: 600;
        transition: 0.2s;
    }}

    .stButton button:hover,
    .stFormSubmitButton button:hover {{
        border: 1px solid #A995FF;
        color: white !important;
        filter: brightness(1.12);
    }}

    div[data-testid="stExpander"] {{
        background-color: {card_bg};
        border: 1px solid {border_color};
        border-radius: 12px;
    }}

    hr {{
        border-color: {border_color};
    }}

    .status-card {{
        background-color: {card_bg};
        border: 1px solid {border_color};
        border-radius: 14px;
        padding: 17px;
        margin-bottom: 12px;
    }}

    .status-title {{
        font-size: 14px;
        color: {muted} !important;
    }}

    .status-value {{
        font-size: 21px;
        font-weight: 700;
        color: {text_color} !important;
    }}

    </style>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <p class="section-label">AI POWERED DATA ANALYSIS</p>
        <h1>Chat With Your CSV</h1>
        <p>
            Explore your data using natural language.
            Ask questions, generate SQL and get instant results.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# CSV UPLOAD
# --------------------------------------------------

st.markdown("### 📂 Upload Your Dataset")

uploaded_file = st.file_uploader(
    "Choose a CSV file",
    type=["csv"],
    help="Upload a CSV file to start exploring your data."
)

if uploaded_file is None:

    st.info("Upload a CSV file to get started.")

    st.markdown(
        """
        ### What you can do

        - Ask questions about your dataset in natural language.
        - Generate SQL using a local Qwen model.
        - Validate and execute SQL through an AI agent.
        - Explore dataset statistics and visualizations.
        - Run your own SQL queries.
        """
    )

    st.stop()


# --------------------------------------------------
# READ AND PREPROCESS CSV
# --------------------------------------------------

try:

    file_bytes = uploaded_file.getvalue()

    file_signature = hashlib.sha256(file_bytes).hexdigest()

    if st.session_state.get("dataset_signature") != file_signature:

        st.session_state.dataset_signature = file_signature

        st.session_state.agent_sql = None
        st.session_state.agent_result = None
        st.session_state.agent_error = None
        st.session_state.manual_result = None
        st.session_state.query_history = []

    from io import BytesIO

    df = pd.read_csv(BytesIO(file_bytes))

    empty_columns = df.columns[df.isna().all()].tolist()

    if empty_columns:
        df = df.drop(columns=empty_columns)

    if df.empty or len(df.columns) == 0:
        st.error("The uploaded CSV contains no usable data.")
        st.stop()

    connection = create_database(df)

except Exception as e:

    st.error(f"Could not process the uploaded CSV: {e}")
    st.stop()


# --------------------------------------------------
# DATASET INFORMATION
# --------------------------------------------------

total_rows = len(df)
total_columns = len(df.columns)
missing_values = int(df.isna().sum().sum())
duplicate_rows = int(df.duplicated().sum())

try:

    schema_df = get_table_schema(connection)
    schema_text = get_schema_text(connection)
    preview = get_table_preview(connection)

except Exception as e:

    connection.close()
    st.error(f"Database error: {e}")
    st.stop()


# --------------------------------------------------
# OVERVIEW PAGE
# --------------------------------------------------

if page == "Overview":

    st.markdown("### 📈 Dataset Overview")
    st.caption("A quick summary of your uploaded data.")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Rows", f"{total_rows:,}")
    c2.metric("Total Columns", total_columns)
    c3.metric("Missing Values", f"{missing_values:,}")
    c4.metric("Duplicate Rows", f"{duplicate_rows:,}")

    st.divider()

    left, right = st.columns([1.5, 1])

    with left:

        st.markdown("### Dataset Preview")

        st.dataframe(
            preview,
            use_container_width=True,
            hide_index=True
        )

    with right:

        st.markdown("### Database Status")

        st.markdown(
            """
            <div class="status-card">
                <div class="status-title">Database</div>
                <div class="status-value">● Connected</div>
            </div>
            <div class="status-card">
                <div class="status-title">Storage Engine</div>
                <div class="status-value">SQLite</div>
            </div>
            <div class="status-card">
                <div class="status-title">AI Agent</div>
                <div class="status-value">LangGraph</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    st.markdown("### 📊 Explore Your Data")

    chart_column = st.selectbox(
        "Choose a column to visualize",
        df.columns,
        key="overview_chart_column"
    )

    if pd.api.types.is_numeric_dtype(df[chart_column]):

        fig = px.histogram(
            df,
            x=chart_column,
            title=f"Distribution of {chart_column}",
            template="plotly_dark" if theme == "Dark" else "plotly_white",
            color_discrete_sequence=["#8B6DFF"]
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=text_color
        )

        st.plotly_chart(fig, use_container_width=True)

    else:

        counts = (
            df[chart_column]
            .fillna("Missing")
            .astype(str)
            .value_counts()
            .head(15)
            .reset_index()
        )

        counts.columns = [chart_column, "Count"]

        fig = px.bar(
            counts,
            x=chart_column,
            y="Count",
            title=f"Top values in {chart_column}",
            template="plotly_dark" if theme == "Dark" else "plotly_white",
            color_discrete_sequence=["#638BFF"]
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=text_color,
            xaxis_title=chart_column
        )

        st.plotly_chart(fig, use_container_width=True)


# --------------------------------------------------
# AI WORKSPACE
# --------------------------------------------------

elif page == "AI Workspace":

    st.markdown("### ✦ AI Query Workspace")

    st.caption(
        "Ask questions in plain English. "
        "Your LangGraph agent will generate, validate and execute SQL."
    )

    st.markdown(
        """
        <div class="status-card">
            <div class="status-title">POWERED BY</div>
            <div class="status-value">
                Qwen + LangChain + LangGraph
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("#### Ask your data anything")

    with st.form("agent_query_form"):

        question = st.text_area(
            "Your question",
            placeholder=(
                "Example: How many records belong to India?"
            ),
            height=100
        )

        submitted = st.form_submit_button(
            "✦ Ask AI Agent",
            type="primary",
            use_container_width=True
        )

    if submitted:

        if not question.strip():

            st.warning("Please enter a question.")

        else:

            st.session_state.agent_sql = None
            st.session_state.agent_result = None
            st.session_state.agent_error = None

            history_entry = {
                "timestamp": datetime.now().strftime("%d %b %Y, %I:%M:%S %p"),
                "question": question.strip(),
                "sql": None,
                "status": "Failed",
                "error": None,
                "columns": [],
                "rows": []
            }

            try:

                with st.spinner(
                    "AI Agent is inspecting your data and processing your question..."
                ):

                    agent = build_agent(connection)

                    response = run_agent(
                        agent,
                        question
                    )

                if response.get("error"):

                    st.session_state.agent_error = response["error"]
                    history_entry["error"] = response["error"]

                else:

                    st.session_state.agent_sql = response["sql"]
                    st.session_state.agent_result = response["result"]
                    st.session_state.agent_question = question

                    history_entry["sql"] = response["sql"]
                    history_entry["status"] = "Success"
                    history_entry["columns"] = response["result"]["columns"]
                    history_entry["rows"] = response["result"]["rows"]

            except Exception as e:

                st.session_state.agent_error = str(e)
                history_entry["error"] = str(e)

            st.session_state.query_history.append(history_entry)

            # Keep only the latest 20 queries.
            st.session_state.query_history = (
                st.session_state.query_history[-20:]
            )

    if st.session_state.agent_error:

        st.error(
            f"Agent execution failed: {st.session_state.agent_error}"
        )

    if st.session_state.agent_sql:

        st.divider()

        st.markdown("### Generated SQL")

        st.success("SQL validated and executed successfully!")

        st.code(
            st.session_state.agent_sql,
            language="sql"
        )

        st.markdown("### Query Results")

        result_data = st.session_state.agent_result

        result_df = pd.DataFrame(
            result_data["rows"],
            columns=result_data["columns"]
        )

        r1, r2 = st.columns(2)

        r1.metric("Rows Returned", len(result_df))
        r2.metric("Result Columns", len(result_df.columns))

        st.dataframe(
            result_df,
            use_container_width=True,
            hide_index=True
        )

        with st.expander("View Agent Workflow"):

            workflow_steps = [
                "Inspect uploaded CSV schema",
                "Generate SQL using Qwen",
                "Validate SQL using SQLGlot",
                "Execute SQL using SQLite",
                "Return results to the user"
            ]

            for i, step in enumerate(workflow_steps, 1):
                st.markdown(f"**{i}.** {step}")


    # --------------------------------------------------
    # QUERY HISTORY
    # --------------------------------------------------

    st.divider()

    st.markdown("### 🕘 Query History")

    st.caption("Your last 20 AI queries for the current dataset.")

    if st.session_state.query_history:

        st.markdown(
            f"**Total queries:** {len(st.session_state.query_history)}"
        )

        for index, entry in enumerate(
            reversed(st.session_state.query_history),
            1
        ):

            status_icon = (
                "✅" if entry["status"] == "Success" else "❌"
            )

            with st.expander(
                f"{status_icon} {entry['question']} "
                f"— {entry['timestamp']}"
            ):

                st.caption(f"Query #{len(st.session_state.query_history) - index + 1}")

                if entry["status"] == "Success":

                    st.success("Query executed successfully.")

                    if entry["sql"]:

                        st.markdown("**Generated SQL**")

                        st.code(
                            entry["sql"],
                            language="sql"
                        )

                    if entry["rows"] is not None:

                        history_df = pd.DataFrame(
                            entry["rows"],
                            columns=entry["columns"]
                        )

                        st.markdown("**Query Results**")

                        st.dataframe(
                            history_df,
                            use_container_width=True,
                            hide_index=True
                        )

                else:

                    st.error("Query execution failed.")

                    if entry["error"]:

                        st.caption(entry["error"])

                    if entry["sql"]:

                        st.code(
                            entry["sql"],
                            language="sql"
                        )

    else:

        st.info(
            "No query history yet. Ask your first question above!"
        )


# --------------------------------------------------
# DATASET EXPLORER
# --------------------------------------------------

elif page == "Dataset Explorer":

    st.markdown("### 🗂 Dataset Explorer")

    tab1, tab2, tab3 = st.tabs(
        ["Data Preview", "Schema", "Manual SQL"]
    )

    with tab1:

        st.markdown("#### Uploaded CSV Data")

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            f"Showing {len(df):,} rows and {len(df.columns)} columns."
        )

    with tab2:

        st.markdown("#### SQLite Table Schema")

        st.code(schema_text, language="sql")

        st.dataframe(
            schema_df,
            use_container_width=True,
            hide_index=True
        )

    with tab3:

        st.markdown("#### Run Your Own SQL")

        st.caption(
            "Only SELECT queries on uploaded_data are allowed."
        )

        with st.form("manual_sql_form"):

            user_query = st.text_area(
                "SQL Query",
                value="SELECT * FROM uploaded_data LIMIT 5;",
                height=140
            )

            manual_submitted = st.form_submit_button(
                "Run SQL Query",
                type="primary"
            )

        if manual_submitted:

            try:

                result = execute_query(
                    connection,
                    user_query
                )

                st.session_state.manual_result = {
                    "query": user_query,
                    "columns": list(result.columns),
                    "rows": result.to_dict(orient="records")
                }

            except Exception as e:

                st.error(f"SQL execution failed: {e}")

        if st.session_state.manual_result:

            manual_data = st.session_state.manual_result

            st.success("SQL query executed successfully!")

            st.code(
                manual_data["query"],
                language="sql"
            )

            manual_df = pd.DataFrame(
                manual_data["rows"],
                columns=manual_data["columns"]
            )

            st.metric("Rows Returned", len(manual_df))

            st.dataframe(
                manual_df,
                use_container_width=True,
                hide_index=True
            )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Chat With Your CSV | Qwen • LangChain • LangGraph • SQLite"
)

connection.close()
