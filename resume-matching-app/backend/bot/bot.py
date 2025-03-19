from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Neo4jVector
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.question_answering import load_qa_chain
from langchain.chains import LLMChain
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
# from langchain_community.graphs import Neo4jGraph
from langchain_neo4j import Neo4jGraph

class ResumeJobMatchingBot:
    def __init__(self, neo4j_uri, neo4j_username, neo4j_password, openai_api_key, groq_api_key=None, use_groq=False):
        """Initialize the Resume-Job Matching Bot."""

        # Connect to Neo4j
        self.graph = Neo4jGraph(
            url=neo4j_uri,
            username=neo4j_username,
            password=neo4j_password
        )
        
        # Initialize embedding model
        self.embeddings = OpenAIEmbeddings(api_key=openai_api_key)
        
        # # Initialize LLM (OpenAI by default, Groq optionally)
        # if use_groq and groq_api_key:
        # if using groqAPI
        self.llm = ChatGroq(temperature=0, model_name="llama3-8b-8192", groq_api_key=groq_api_key)
        # else:
        # if using openAI
        # self.llm = ChatOpenAI(temperature=0, model_name="gpt-4", api_key=openai_api_key)
        
        # Set up vector store
        self.vector_store = Neo4jVector.from_existing_graph(
            embedding=self.embeddings,
            graph=self.graph,
            node_label="Person",
            text_node_properties=["name", "email"],
            embedding_node_property="embedding"
        )
        
        # Create job vector store
        self.job_vector_store = Neo4jVector.from_existing_graph(
            embedding=self.embeddings,
            graph=self.graph,
            node_label="Job",
            text_node_properties=["title", "description"],
            embedding_node_property="job_embedding"
        )

        print(f"Neo4j URI: {neo4j_uri}")  # Debugging output


    def initialize_indexes(self):
        """Create necessary Neo4j indexes for efficient graph traversal."""
        # Create indexes
        self.graph.query("CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.email)")
        self.graph.query("CREATE INDEX IF NOT EXISTS FOR (s:Skill) ON (s.name)")
        self.graph.query("CREATE INDEX IF NOT EXISTS FOR (j:Job) ON (j.title)")
        
        # Create vector index if not exists
        vector_index_query = """
        CALL db.index.vector.createNodeIndex(
          'resume_vector_index',
          'Person',
          'embedding',
          1536,
          'cosine'
        )
        """
        try:
            self.graph.query(vector_index_query)
        except:
            # Index might already exist
            pass
            
        job_vector_index_query = """
        CALL db.index.vector.createNodeIndex(
          'job_vector_index',
          'Job',
          'job_embedding',
          1536,
          'cosine'
        )
        """
        try:
            self.graph.query(job_vector_index_query)
        except:
            # Index might already exist
            pass
    
    def get_candidate_graph_context(self, person_email):
        """Get comprehensive graph context for a candidate."""
        query = """
        MATCH (p:Person {email: $email})
        OPTIONAL MATCH (p)-[:HAS_SKILL]->(s:Skill)
        OPTIONAL MATCH (p)-[:HAS_EDUCATION]->(e:Education)
        OPTIONAL MATCH (p)-[:HAS_EXPERIENCE]->(r:Role)
        OPTIONAL MATCH (p)-[:PROJECT_DONE]->(pr:Project)
        RETURN p.name as name, p.email as email,
               collect(distinct s.name) as skills,
               collect(distinct {degree: e.degree, institution: e.institution, year: e.graduation_year}) as education,
               collect(distinct {title: r.title, company: r.company, years: r.years, description: r.description}) as roles,
               collect(distinct pr.title) as projects
        """
        result = self.graph.query(query, {"email": person_email})
        return result[0] if result else None
    
    def get_job_details(self, job_title):
        """Get comprehensive job details including required skills."""
        query = """
        MATCH (j:Job {title: $title})
        OPTIONAL MATCH (j)-[:REQUIRES_SKILL]->(s:Skill)
        RETURN j.title as title, j.description as description,
               collect(distinct s.name) as required_skills
        """
        result = self.graph.query(query, {"title": job_title})
        return result[0] if result else None
    
    def find_matching_candidates(self, job_title, min_skill_match=0.6, limit=10):
        """Find candidates matching a job based on skill overlap."""
        query = """
        MATCH (j:Job {title: $job_title})-[:REQUIRES_SKILL]->(s:Skill)<-[:HAS_SKILL]-(p:Person)
        WITH j, p, count(s) AS matching_skills
        MATCH (j)-[:REQUIRES_SKILL]->(all_skills:Skill)
        WITH j, p, matching_skills, count(all_skills) AS total_required_skills
        WITH j, p, matching_skills, total_required_skills, 
             toFloat(matching_skills) / total_required_skills AS match_ratio
        WHERE match_ratio >= $min_match
        RETURN p.name AS name, p.email AS email, matching_skills, total_required_skills, 
               match_ratio AS skill_match_ratio
        ORDER BY skill_match_ratio DESC
        LIMIT $limit
        """
        result = self.graph.query(query, {
            "job_title": job_title, 
            "min_match": min_skill_match,
            "limit": limit
        })
        return result
    
    def advanced_candidate_matching(self, job_title, experience_weight=0.3, education_weight=0.2, skill_weight=0.5):
        """
        Advanced matching algorithm that considers skills, education, and experience
        with customizable weights for each factor.
        """
        query = """
        MATCH (j:Job {title: $job_title})-[:REQUIRES_SKILL]->(required:Skill)
        WITH j, collect(required.name) AS required_skills
        
        MATCH (p:Person)
        OPTIONAL MATCH (p)-[:HAS_SKILL]->(s:Skill)
        WITH j, p, required_skills, collect(s.name) AS candidate_skills
        
        // Calculate skill match score
        WITH j, p, required_skills, candidate_skills,
             size([x IN candidate_skills WHERE x IN required_skills]) AS matching_skills,
             size(required_skills) AS total_required
        
        // Calculate skill match ratio
        WITH j, p, toFloat(matching_skills) / total_required AS skill_ratio
        
        // Get candidate education
        OPTIONAL MATCH (p)-[:HAS_EDUCATION]->(e:Education)
        WITH j, p, skill_ratio, collect(e) AS educations
        
        // Calculate education score (example: higher for advanced degrees)
        WITH j, p, skill_ratio,
             reduce(score = 0.0, ed IN educations | 
                score + CASE 
                    WHEN ed.degree CONTAINS 'PhD' THEN 1.0
                    WHEN ed.degree CONTAINS 'Master' THEN 0.8
                    WHEN ed.degree CONTAINS 'Bachelor' THEN 0.6
                    ELSE 0.3
                END) / 
             CASE WHEN size(educations) > 0 THEN size(educations) ELSE 1 END AS education_score
        
        // Get candidate experience
        OPTIONAL MATCH (p)-[:HAS_EXPERIENCE]->(r:Role)
        WITH j, p, skill_ratio, education_score, collect(r) AS roles
        
        // Calculate experience score (example: based on years of experience)
        WITH j, p, skill_ratio, education_score,
             reduce(score = 0.0, r IN roles | score + r.years) AS total_experience,
             size(roles) AS num_roles
        
        // Normalize experience (cap at 10 years)
        WITH j, p, skill_ratio, education_score, 
             CASE WHEN total_experience > 10 THEN 1.0 ELSE total_experience / 10 END AS experience_score
        
        // Calculate weighted score
        WITH p, skill_ratio, education_score, experience_score,
             $skill_weight * skill_ratio + 
             $education_weight * education_score + 
             $experience_weight * experience_score AS combined_score
        
        RETURN p.name AS name, p.email AS email, 
               skill_ratio AS skill_match, 
               education_score AS education_score,
               experience_score AS experience_score,
               combined_score AS overall_match
        ORDER BY combined_score DESC
        LIMIT 20
        """
        
        result = self.graph.query(query, {
            "job_title": job_title, 
            "skill_weight": skill_weight,
            "education_weight": education_weight,
            "experience_weight": experience_weight
        })
        return result
    
    def semantic_job_match(self, job_title, query_text, top_k=5):
        """Find candidates based on semantic matching of their resume to a job plus a query."""
        # Get job description
        job = self.get_job_details(job_title)
        if not job:
            return []
        
        # Augment query with job context
        augmented_query = f"Job Title: {job['title']}\nJob Description: {job['description']}\nRequired Skills: {', '.join(job['required_skills'])}\nQuery: {query_text}"
        
        # Perform semantic search in vector store
        similar_people = self.vector_store.similarity_search_with_score(
            augmented_query, k=top_k
        )
        
        results = []
        for doc, score in similar_people:
            person_email = doc.metadata.get('email')
            candidate_details = self.get_candidate_graph_context(person_email)
            if candidate_details:
                results.append({
                    "candidate": candidate_details,
                    "similarity_score": score
                })
        
        return results
        
    def chat_response(self, query, job_title=None):
        """Generate a chat response for the given query about candidates for a job."""
        system_prompt = """
        You are an AI HR assistant specialized in candidate-job matching. Analyze the candidate 
        profiles and job requirements to provide accurate matches and insights.
        
        Job Details: {job_details}
        
        Candidate Matches: {candidate_matches}
        
        Based on this graph database information, provide a detailed, professional analysis. If no match is found just say I don't know.
        """
        
        user_prompt = """{query}"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_prompt)
        ])
        
        # Get job details
        job_details = "No job specified"
        if job_title:
            job_data = self.get_job_details(job_title)
            if job_data:
                job_details = f"Title: {job_data['title']}\nDescription: {job_data['description']}\nRequired Skills: {', '.join(job_data['required_skills'])}"
        
        # Get candidate matches
        candidate_matches = "No candidates found"
        if job_title:
            candidates = self.advanced_candidate_matching(job_title)
            if candidates:
                candidate_matches = ""
                for i, candidate in enumerate(candidates[:5], 1):
                    candidate_details = self.get_candidate_graph_context(candidate["email"])
                    if candidate_details:
                        candidate_matches += f"\n--- Candidate {i}: {candidate['name']} ---\n"
                        candidate_matches += f"Match Score: {candidate['overall_match']:.2f}\n"
                        candidate_matches += f"Skills: {', '.join(candidate_details['skills'])}\n"
        
        chain = prompt | self.llm
        response = chain.invoke({
            "query": query,
            "job_details": job_details,
            "candidate_matches": candidate_matches
        })
        
        if isinstance(response, dict) and "content" in response:
            return response["content"]
        return response

    def retrieve_graph_info(self, query):
        """
        Takes a user query and converts it to a Cypher query using the schema information,
        then executes it against the Neo4j graph database.
        
        Args:
            self: The class instance
            query: The user's natural language query
            
        Returns:
            The results from the Neo4j graph database
        """
       
        # Schema definition
        schema = """
        # Nodes:
        Person {email: STRING, name: STRING}
        Skill {name: STRING}
        Education {degree: STRING, institution: STRING, graduation_year: INTEGER}
        Project {title: STRING}
        Role {description: STRING, company: STRING, years: INTEGER, title: STRING}
        Job {description: STRING, title: STRING}
        # Relationships:
        (:Person)-[:HAS_SKILL]->(:Skill)
        (:Person)-[:HAS_EDUCATION]->(:Education)
        (:Person)-[:HAS_EXPERIENCE]->(:Role)
        (:Person)-[:PROJECT_DONE]->(:Project)
        (:Job)-[:REQUIRES_SKILL]->(:Skill)
        """
        
        # Enhanced prompt with examples and best practices
        cypher_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at converting natural language questions into Cypher queries for Neo4j graph databases.
            
            Guidelines for generating high-quality Cypher queries:
            1. Use appropriate pattern matching to navigate the graph
            2. Use WHERE clauses to filter results when necessary
            3. Include RETURN statements with meaningful aliases
            4. Use ORDER BY, LIMIT, or aggregation functions when appropriate
            5. For complex queries, consider using WITH clauses to pipe results
            6. Return only the information that directly answers the question
            7. Generate executable Cypher code only, no explanations
            8. Convert the question to lower case and no escape sequences like - \n
            """),
            (
                "human",
                (
                    "Based on the Neo4j graph schema below, write a Cypher query that would answer the user's question:\n\n"
                    "{schema}\n\n"
                    "Example queries:\n"
                    "1. Question: Find people who know python\n"
                    "   Cypher: MATCH (p:Person)-[:HAS_SKILL]->(s:Skill) WHERE s.name = 'python' RETURN p.name\n"
                    "2. Question: Which skills are most in demand for jobs?\n"
                    "   Cypher: MATCH (:Job)-[:REQUIRES_SKILL]->(s:Skill) RETURN s.name, count(*) as demand ORDER BY demand DESC\n\n"
                    "Question: {query}\n"
                    "Cypher query:"
                ),
            ),
        ])
        
        # Create the chain to generate the Cypher query
        # cypher_chain = LLMChain(
        #     llm=self.llm,
        #     prompt=cypher_prompt
        # )

        cypher_chain = cypher_prompt|self.llm
        
        # Generate the Cypher query
        # below is for groq
        cypher_query = cypher_chain.invoke({
            "schema": schema,
            "query": query
        })
        # below is for openAI
        # cypher_query = cypher_chain.invoke({
        #     "schema": schema,
        #     "query": query
        # })["text"].strip()
        
        # Execute the Cypher query against the Neo4j database
        try:
            results = self.graph.query(cypher_query.content)
            return {
                "query": query,
                "cypher_query": cypher_query,
                "results": results
            }
        except Exception as e:
            return {
                "query": query,
                "cypher_query": cypher_query,
                "error": str(e),
                "results": []
            }
