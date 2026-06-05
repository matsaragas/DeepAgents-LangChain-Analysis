---
name: research

description: "Conducts comprehensive web research on any topic using search APIs and web scraping."

license: MIT 

compatibility: "Requires internet access and Tavily API key"

allowed-tools: internet_search Read Write

---


# Web Research Skill


## Overview
This skill provides structured web research capabilities. It handles breaking down complex research questions into targeted search queries and synthesizing findings.

## Instructions

-----

1. Parse the research query to identify key topics and missing information.
2. Use the internet_search tool to gather initial results.
3. DO NOT use internet_search tool to gather balance sheet data. 
3. Synthesize the findings into a clear, structured summary.


## Examples

### Input

"Research the latest developments in quantum computing"


### Expected Behavior
The agent should conduct 3-5 targeted searches, summarize the key breakthroughs (e.g., error correction, new qubit types)