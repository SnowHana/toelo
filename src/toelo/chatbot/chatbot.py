import os
from getpass import getpass
from dotenv import load_dotenv

from typing_extensions import Annotated
from typing_extensions import TypedDict

from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.chat_models import ChatOllama

from langgraph.graph import START, StateGraph

from langgraph.checkpoint.memory import MemorySaver

from toelo.player_elo.database_connection import get_connection_string, DATABASE_CONFIG


class QueryOutput(TypedDict):
    """Generated SQL query

    Args:
        TypedDict (_type_): _description_
    """

    query: Annotated[str, ..., "Syntatically valid SQL Query"]


class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str


class BaseChatBot:
    def __init__(self, chatbot_name: str):
        load_dotenv()
        if not os.environ.get("LANGSMITH_API_KEY"):
            os.environ["LANGSMITH_API_KEY"] = getpass()
            os.environ["LANGSMITH_API_KEY"] = "true"

        # Init db
        db_uri = get_connection_string(DATABASE_CONFIG)
        self.db = SQLDatabase.from_uri(db_uri)

        self._init_llm(chatbot_name)

    def _init_llm(self, chatbot_name: str):
        # choice = input("Enter models to choose: (gemini / codegemma)")
        if "gemini" in chatbot_name.lower():
            self._init_gemini_llm()
        else:
            self._init_olama_llm()

    def _init_gemini_llm(self):
        if not os.environ.get("GOOGLE_API_KEY"):
            os.environ["GOOGLE_API_KEY"] = getpass.getpass(
                "Enter API key for Google Gemini: "
            )

        self.llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai")

    def _init_olama_llm(self):
        self.llm = ChatOllama(model="codegemma:7b")


class ChatBot(BaseChatBot):
    def __init__(self):
        # load_dotenv()
        # if not os.environ.get("LANGSMITH_API_KEY"):
        #     os.environ["LANGSMITH_API_KEY"] = getpass()
        #     os.environ["LANGSMITH_API_KEY"] = "true"

        # # Init db
        # db_uri = get_connection_string(DATABASE_CONFIG)
        # self.db = SQLDatabase.from_uri(db_uri)

        # self._init_llm()
        super().__init__()
        self._init_query_prompt_template()
        self._init_graph()

        # Init llm

    def _init_gemini_llm(self):
        if not os.environ.get("GOOGLE_API_KEY"):
            os.environ["GOOGLE_API_KEY"] = getpass.getpass(
                "Enter API key for Google Gemini: "
            )

        self.llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai")

    def _init_query_prompt_template(self):
        system_message = """
        Given an input question, create a syntactically correct {dialect} query to
        run to help find the answer. Unless the user specifies in his question a
        specific number of examples they wish to obtain, always limit your query to
        at most {top_k} results. You can order the results by a relevant column to
        return the most interesting examples in the database.

        Never query for all the columns from a specific table, only ask for a the
        few relevant columns given the question.

        Pay attention to use only the column names that you can see in the schema
        description. Be careful to not query for columns that do not exist. Also,
        pay attention to which column is in which table.

        Only use the following tables:
        {table_info}
        """

        user_prompt = "Question: {input}"

        self.query_prompt_template = ChatPromptTemplate(
            [("system", system_message), ("user", user_prompt)]
        )

    def _write_query(self, state: State):
        """Generate SQL query to fetch info

        Change top_k to get different number of results.

        Args:
            state (State): _description_
        """
        prompt = self.query_prompt_template.invoke(
            {
                "dialect": self.db.dialect,
                "top_k": 10,
                "table_info": self.db.get_table_info(),
                "input": state["question"],
            }
        )
        # print(prompt)
        structured_llm = self.llm.with_structured_output(QueryOutput)
        result = structured_llm.invoke(prompt)
        return {"query": result["query"]}

    def _execute_query(self, state: State):
        """Exectues SQL query

        Args:
            state (State): _description_
        """

        execute_query_tool = QuerySQLDataBaseTool(db=self.db)
        return {"result": execute_query_tool.invoke(state["query"])}

    def _generate_answer(self, state: State):
        """Answer question using retrieved info as context

        Args:
            state (State): _description_
        """
        prompt = (
            "Given the following user question, corresponding SQL query, "
            "and SQL result, answer the user question.\n\n"
            f'Question: {state["question"]}\n'
            f'SQL Query: {state["query"]}\n'
            f'SQL Result: {state["result"]}'
        )
        response = self.llm.invoke(prompt)
        return {"answer": response.content}

    def _init_graph(self):
        memory = MemorySaver()
        graph_builder = StateGraph(State).add_sequence(
            [self._write_query, self._execute_query, self._generate_answer]
        )
        graph_builder.add_edge(START, "_write_query")
        self.graph = graph_builder.compile(
            checkpointer=memory, interrupt_before=["_execute_query"]
        )
        self.graph_config: dict[str, dict[str, int]] = {
            "configurable": {"thread_id": 1}
        }

    def run_graph(self, question: str):
        """Main mehtod to run through our steps of generating and executing a SQL query
        to get a result.

        Args:
            question (str): _description_
        """
        for step in self.graph.stream(
            {"question": question},
            self.graph_config,
            stream_mode="updates",
        ):
            print(step)

        try:
            user_approval = input("Do you want to execute query? y/n: ")
        except Exception:
            user_approval = "n"

        if user_approval.lower() == "y":
            # Continue graph execution
            for step in self.graph.stream(
                None, self.graph_config, stream_mode="updates"
            ):
                print(step)
        else:
            print("Operation Cancelled by user")


# print(c.run_graph("Player with not-null, highest player elo?"))
