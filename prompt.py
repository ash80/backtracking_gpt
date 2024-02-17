import time
from pydantic import BaseModel
from typing import Any, Callable, List
from langchain.prompts.chat import BaseChatPromptTemplate
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.vectorstores.base import VectorStoreRetriever


class ChatGPTPrompt(BaseChatPromptTemplate, BaseModel):
    ai_name: str
    ai_role: str
    token_counter: Callable[[str], int]
    send_token_limit: int = 4196


    def format_messages(self, **kwargs: Any) -> List[BaseMessage]:
        system_prompts = []
        system_prompts.append(SystemMessage(content=f"You are {self.ai_name}, {self.ai_role}\n"))
        system_prompts.append(SystemMessage(
            content=f"The current time and date is {time.strftime('%c')}\n"
        ))
        system_prompts.append(SystemMessage(content=f"Help the user with the following query:\n"))
        user_message = HumanMessage(content=kwargs["query"])
        used_tokens = self.token_counter("".join(map(lambda x: x.content, system_prompts))) + self.token_counter(
            user_message.content
        )
        memory: VectorStoreRetriever = kwargs["memory"]
        previous_messages: List[BaseMessage] = kwargs["messages"]
        if previous_messages:
            relevant_docs = memory.get_relevant_documents(str(previous_messages[-10:]))
            relevant_memory = [d.page_content for d in relevant_docs]
            relevant_memory_tokens = sum(
                [self.token_counter(doc) for doc in relevant_memory]
            )
            while used_tokens + relevant_memory_tokens > 2500:
                relevant_memory = relevant_memory[:-1]
                relevant_memory_tokens = sum(
                    [self.token_counter(doc) for doc in relevant_memory]
                )
            content_format = (
                f"This reminds you of these events "
                f"from your past:\n{relevant_memory}\n\n"
            )
            memory_message = SystemMessage(content=content_format)
            used_tokens += self.token_counter(memory_message.content)

            historical_messages: List[BaseMessage] = []
            for message in previous_messages[-10:][::-1]:
                message_tokens = self.token_counter(message.content)
                if used_tokens + message_tokens > self.send_token_limit - 1000:
                    break
                historical_messages = [message] + historical_messages
                used_tokens += message_tokens
        messages: List[BaseMessage] = system_prompts + [user_message]

        if previous_messages:
            messages.append(memory_message)
            messages += historical_messages
            previous_messages.append(user_message)
        else:
            previous_messages += system_prompts + [user_message]
        return messages
