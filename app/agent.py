from typing import TypedDict, List
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from tavily import TavilyClient
from app.config import get_settings

settings = get_settings()

# Initialize clients
tavily = TavilyClient(api_key=settings.tavily_api_key)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0,
    google_api_key=settings.google_api_key
)


class Source(BaseModel):
    url: str = Field(description="URL of the source article")
    title: str = Field(description="Title of the source article")


class AgentState(TypedDict):
    industry: str
    raw_data: List[str]
    sources: List[dict]
    risk_report: str
    critical_alerts: List[str]
    fragility_score: int
    risk_metrics: List[dict]


class RiskMetric(BaseModel):
    category: str = Field(description="e.g., Logistics, Labor, Geopolitical")
    impact_score: int = Field(description="Scale of 1-10")
    description: str = Field(description="Brief explanation of the risk")


class AnalystOutput(BaseModel):
    executive_summary: str
    fragility_score: int = Field(description="Overall 1-10 score for the industry")
    risk_metrics: List[RiskMetric]
    critical_alerts: List[str]
    sources: List[Source] = Field(description="List of source articles used in the analysis")


def researcher_node(state):
    """Search for recent supply chain disruptions based on the industry"""
    industry = state.get("industry", "Global")
    query = f"recent supply chain disruptions, port strikes, and logistics risks in {industry} industry 2025"

    print(f"--- AGENT RESEARCHING: {query} ---")

    search_result = tavily.search(
        query=query, 
        topic="news", 
        search_depth="advanced",
        max_results=5
    )

    raw_data = [
        f"Source: {r['url']}\nContent: {r['content']}" 
        for r in search_result['results']
    ]
    
    sources = [
        {
            'url': r['url'],
            'title': r.get('title', r['url'])
        }
        for r in search_result['results']
    ]

    return {"raw_data": raw_data, "sources": sources}


def risk_analyst_node(state):
    """Analyze research data and generate risk report"""
    raw_text = "\n\n".join(state["raw_data"])
    industry = state["industry"]
    
    system_prompt = f"""
    You are a Senior Supply Chain Risk Analyst for a C-suite executive team.
    Analyze the provided research regarding the {industry} industry.

    Your goal:
    1. Identify specific disruptions (strikes, shortages, delays).
    2. Quantify the 'Fragility Score' (1-10).
    3. Categorize risks into Logistics, Labor, or Geopolitical.
    4. Provide a punchy Executive Summary.
    """

    structured_llm = llm.with_structured_output(AnalystOutput)

    analysis = structured_llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": raw_text}
    ])

    return {
        "risk_report": analysis.executive_summary,
        "fragility_score": analysis.fragility_score,
        "critical_alerts": analysis.critical_alerts,
        "risk_metrics": [m.model_dump() for m in analysis.risk_metrics],
        "sources": [s.model_dump() for s in analysis.sources]
    }


# Build the graph
workflow = StateGraph(AgentState)
workflow.add_node("researcher", researcher_node)
workflow.add_node("analyst", risk_analyst_node)

workflow.add_edge(START, "researcher")
workflow.add_edge("researcher", "analyst")
workflow.add_edge("analyst", END)

supply_chain_app = workflow.compile()
