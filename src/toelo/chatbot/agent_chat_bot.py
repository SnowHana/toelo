from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent


from toelo.chatbot.chatbot import BaseChatBot


class AgentChatBot(BaseChatBot):
    def __init__(self, chatbot_name: str):
        super().__init__(chatbot_name=chatbot_name)
        toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.tools = toolkit.get_tools()

        self._init_system_message()
        self._init_agent_executor()

    def _init_system_message(self):

        self.system_message = """
        You are an agent designed to interact with a SQL database.
        Given an input question, create a syntactically correct {dialect} query to run,
        then look at the results of the query and return the answer. Unless the user
        specifies a specific number of examples they wish to obtain, always limit your
        query to at most {top_k} results.

        You can order the results by a relevant column to return the most interesting
        examples in the database. Never query for all the columns from a specific table,
        only ask for the relevant columns given the question.

        You MUST double check your query before executing it. If you get an error while
        executing a query, rewrite the query and try again.

        DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the
        database.


        Below is the description of tools available.

        sql_db_query: Input to this tool is a detailed and correct SQL query, output is a result from the database. If the query is not correct, an error message will be returned. If an error is returned, rewrite the query, check the query, and try again. If you encounter an issue with Unknown column 'xxxx' in 'field list', use sql_db_schema to query the correct table fields.

        sql_db_schema: Input to this tool is a comma-separated list of tables, output is the schema and sample rows for those tables. Be sure that the tables actually exist by calling sql_db_list_tables first! Example Input: table1, table2, table3

        sql_db_list_tables: Input is an empty string, output is a comma-separated list of tables in the database.

        sql_db_query_checker: Use this tool to double check if your query is correct before executing it. Always use this tool before executing a query with sql_db_query!



        To start you should ALWAYS look at the tables in the database to see what you
        can query. Do NOT skip this step.

        You can use sql_db_list_tables to list all the tables and use sql_db_schema to see the schema and sample rows for those tables.

        Then you should query the schema of the most relevant tables.
        """.format(
            dialect=self.db.dialect,
            top_k=5,
        )

    def _init_agent_executor(self):
        # Init agent
        self.agent_executor = create_react_agent(
            self.llm, self.tools, prompt=self.system_message
        )

    def ask_question(self, question: str):
        res = []
        for step in self.agent_executor.stream(
            {"messages": [{"role": "user", "content": question}]}, stream_mode="values"
        ):
            messages = step["messages"][-1].pretty_repr()
            res.append(messages)
        return res

        # print(result)

        # res = []
        # for step in result:
        #     res.append(step["messages"][-1].pretty_print())
        # # for step in self.agent_executor.stream(
        # #     {"messages": [{"role": "user", "content": question}]},
        # #     stream_mode="values",
        # # ):
        # # step["messages"][-1].pretty_print()
        # print(res)
        # return res


# a = AgentChatBot()
# a.ask_question(
#     "Which country has the highest average player elo where country has at least 20 players?"
# )
