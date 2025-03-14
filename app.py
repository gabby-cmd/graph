import streamlit as st
import os
import pandas as pd
from knowledge_graph import KnowledgeGraph
from document_processor import DocumentProcessor
from query_engine import QueryEngine
from graph_visualization import create_graph_visualization, create_entity_network
import google.generativeai as genai

if 'kg' not in st.session_state:
    st.session_state.kg = KnowledgeGraph()
    st.session_state.processor = DocumentProcessor(st.session_state.kg)
    st.session_state.query_engine = QueryEngine(st.session_state.kg)
    st.session_state.loaded_files = []
    st.session_state.last_query = None
    st.session_state.last_result = None
    st.session_state.chat_history = []

st.title("Knowledge Graph System")
st.markdown("""
This application allows you to:
1. Load and process documents to extract entities and relationships
2. Visualize the knowledge graph
3. Query the knowledge graph for information
4. Chat with Gemini AI about your knowledge graph
""")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Document Processing", "Knowledge Graph", "Query System", "Gemini Chat", "Debug & Stats"])

if page == "Document Processing":
    st.header("Document Processing")

    if st.button("Load Sample Bank Policies"):
        with st.spinner("Loading sample documents..."):
            results = st.session_state.processor.load_sample_documents()
            st.session_state.loaded_files = list(results.keys())
            st.success(f"Loaded {len(results)} sample documents")
            st.balloons()

    st.subheader("Upload Custom Documents")
    uploaded_file = st.file_uploader("Choose a text file", type="txt")

    if uploaded_file is not None:
        document_type = st.selectbox("Document Type", ["banking_policy", "generic"])
        
        if st.button("Process Document"):
            with st.spinner("Processing document..."):
                content = uploaded_file.read().decode("utf-8")
                result = st.session_state.processor.process_document(content, uploaded_file.name, document_type)
                
                if uploaded_file.name not in st.session_state.loaded_files:
                    st.session_state.loaded_files.append(uploaded_file.name)
                
                st.success(f"Document processed successfully!")
                st.json(result)

    if st.session_state.loaded_files:
        st.subheader("Loaded Documents")
        for file in st.session_state.loaded_files:
            st.write(f"- {file}")

    st.subheader("Save/Load Knowledge Graph")
    col1, col2 = st.columns(2)

    with col1:
        save_filename = st.text_input("Save Filename", "knowledge_graph.json")
        if st.button("Save Knowledge Graph"):
            with st.spinner("Saving..."):
                st.session_state.kg.save(save_filename)
                st.success(f"Knowledge graph saved to {save_filename}")

    with col2:
        load_filename = st.text_input("Load Filename", "knowledge_graph.json")
        if st.button("Load Knowledge Graph"):
            with st.spinner("Loading..."):
                if st.session_state.kg.load(load_filename):
                    st.success(f"Knowledge graph loaded from {load_filename}")
                    policy_entities = [e for e in st.session_state.kg.entities if e.type == "Policy"]
                    st.session_state.loaded_files = [e.properties.get("filename", f"Policy {i+1}") 
                                                    for i, e in enumerate(policy_entities)]
                else:
                    st.error(f"File {load_filename} not found")

elif page == "Knowledge Graph":
    st.header("Knowledge Graph Visualization")

    if not st.session_state.kg.entities:
        st.warning("No data in the knowledge graph. Please load or process documents first.")
        if st.button("Load Sample Bank Policies"):
            with st.spinner("Loading sample documents..."):
                results = st.session_state.processor.load_sample_documents()
                st.session_state.loaded_files = list(results.keys())
                st.success(f"Loaded {len(results)} sample documents")
                st.experimental_rerun()
    else:
        stats = st.session_state.kg.get_stats()
        st.subheader("Knowledge Graph Statistics")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Entities", stats["entity_count"])
        col2.metric("Relationships", stats["relationship_count"])
        col3.metric("Text Chunks", stats["text_chunk_count"])
        
        st.subheader("Entity Types")
        entity_types_df = pd.DataFrame({
            "Entity Type": list(stats["entity_types"].keys()),
            "Count": list(stats["entity_types"].values())
        })
        st.bar_chart(entity_types_df.set_index("Entity Type"))
        
        st.subheader("Relationship Types")
        rel_types_df = pd.DataFrame({
            "Relationship Type": list(stats["relationship_types"].keys()),
            "Count": list(stats["relationship_types"].values())
        })
        st.bar_chart(rel_types_df.set_index("Relationship Type"))
        
        st.subheader("Graph Visualization")
        
        entity_types = ["All"] + list(stats["entity_types"].keys())
        selected_type = st.selectbox("Filter by Entity Type", entity_types)
        
        with st.spinner("Generating visualization..."):
            if selected_type == "All" or not selected_type:
                graph_image = create_graph_visualization(st.session_state.kg)
            else:
                filtered_entities = [e.id for e in st.session_state.kg.entities if e.type == selected_type]
                graph_image = create_graph_visualization(st.session_state.kg, highlight_entities=filtered_entities)
            
            st.image(graph_image)
        
        st.subheader("Entity Explorer")
        
        entity_by_type = {}
        for entity in st.session_state.kg.entities:
            if entity.type not in entity_by_type:
                entity_by_type[entity.type] = []
            entity_by_type[entity.type].append((entity.id, entity.name))
        
        selected_entity_type = st.selectbox("Select Entity Type", list(entity_by_type.keys()))
        
        if selected_entity_type:
            entity_options = entity_by_type[selected_entity_type]
            selected_entity = st.selectbox(
                "Select Entity", 
                options=[e[0] for e in entity_options],
                format_func=lambda x: next((e[1] for e in entity_options if e[0] == x), x)
            )
            
            if selected_entity:
                entity = st.session_state.kg.get_entity(selected_entity)
                st.json(entity.to_dict())
                
                st.subheader(f"Network around {entity.name}")
                depth = st.slider("Relationship Depth", 1, 3, 1)
                
                with st.spinner("Generating network visualization..."):
                    entity_network = create_entity_network(st.session_state.kg, entity.id, depth)
                    st.image(entity_network)

elif page == "Query System":
    st.header("Query Knowledge Graph")

    if not st.session_state.kg.entities:
        st.warning("No data in the knowledge graph. Please load or process documents first.")
        if st.button("Load Sample Bank Policies"):
            with st.spinner("Loading sample documents..."):
                results = st.session_state.processor.load_sample_documents()
                st.session_state.loaded_files = list(results.keys())
                st.success(f"Loaded {len(results)} sample documents")
                st.experimental_rerun()
    else:
        st.subheader("Example Questions")
        example_questions = st.session_state.query_engine.get_example_questions()
        
        cols = st.columns(len(example_questions))
        selected_example = None
        
        for i, col in enumerate(cols):
            if col.button(example_questions[i], key=f"example_{i}"):
                selected_example = example_questions[i]
        
        query = st.text_input("Ask a question", value=selected_example if selected_example else "")
        
        if st.button("Search") or selected_example:
            if query:
                with st.spinner("Searching knowledge graph..."):
                    result = st.session_state.query_engine.query(query)
                    st.session_state.last_query = query
                    st.session_state.last_result = result
        
        if st.session_state.last_query and st.session_state.last_result:
            st.subheader("Answer")
            st.write(st.session_state.last_result["answer"])
            
            st.subheader("Sources")
            
            if st.session_state.last_result["entities"]:
                st.write("Relevant Entities:")
                for entity in st.session_state.last_result["entities"]:
                    st.write(f"- **{entity['name']}** ({entity['type']})")
            
            if st.session_state.last_result["chunks"]:
                st.write("Relevant Text Chunks:")
                for chunk in st.session_state.last_result["chunks"]:
                    with st.expander(f"Source: {chunk['metadata'].get('source', 'Unknown')}"):
                        st.write(chunk["text"])
                        st.write(f"Relevance: {chunk['similarity']:.2f}")

elif page == "Gemini Chat":
    st.header("Chat with Gemini AI")
    
    api_key = st.text_input("Enter your Gemini API Key", type="password")
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            
            if "chat_session" not in st.session_state:
                st.session_state.chat_session = model.start_chat(
                    history=[
                        {
                            "role": "user",
                            "parts": ["You are a helpful assistant that specializes in knowledge graphs. Help me understand and work with my knowledge graph data."]
                        },
                        {
                            "role": "model",
                            "parts": ["I'm your knowledge graph specialist assistant. I can help you understand concepts related to knowledge graphs, entity relationships, and how to effectively query and analyze your graph data. What would you like to know about your knowledge graph?"]
                        }
                    ]
                )
            
            if "messages" not in st.session_state:
                st.session_state.messages = [
                    {"role": "assistant", "content": "I'm your knowledge graph specialist assistant. How can I help you today?"}
                ]
            
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            
            if prompt := st.chat_input("What would you like to know about knowledge graphs?"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        kg_stats = st.session_state.kg.get_stats() if st.session_state.kg.entities else {"entity_count": 0, "relationship_count": 0}
                        context = f"The current knowledge graph has {kg_stats.get('entity_count', 0)} entities and {kg_stats.get('relationship_count', 0)} relationships."
                        
                        full_prompt = f"{context}\n\nUser question: {prompt}"
                        response = st.session_state.chat_session.send_message(full_prompt)
                        response_text = response.text
                        
                        st.markdown(response_text)
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
        
        except Exception as e:
            st.error(f"Error with Gemini API: {str(e)}")
            st.info("Please check your API key or try again later.")
    else:
        st.info("Please enter your Gemini API key to start chatting. You can get one from https://makersuite.google.com/")
        
        with st.expander("How to get a Gemini API key"):
            st.markdown("""
            1. Go to [Google AI Studio](https://makersuite.google.com/)
            2. Sign in with your Google account
            3. Click on "Get API key" in the top right corner
            4. Create a new API key or use an existing one
            5. Copy the API key and paste it in the field above
            """)

else:
    st.header("Debug & Statistics")

    st.subheader("Knowledge Graph Statistics")

    if not st.session_state.kg.entities:
        st.warning("No data in the knowledge graph. Please load or process documents first.")
    else:
        stats = st.session_state.kg.get_stats()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Entities", stats["entity_count"])
        col2.metric("Relationships", stats["relationship_count"])
        col3.metric("Text Chunks", stats["text_chunk_count"])
        
        st.subheader("Entities by Type")
        st.bar_chart(pd.DataFrame({
            "Count": list(stats["entity_types"].values())
        }, index=list(stats["entity_types"].keys())))
        
        st.subheader("Relationships by Type")
        st.bar_chart(pd.DataFrame({
            "Count": list(stats["relationship_types"].values())
        }, index=list(stats["relationship_types"].keys())))

    st.subheader("Data Explorer")

    data_type = st.selectbox("Select Data Type", ["Entities", "Relationships", "Text Chunks"])

    if data_type == "Entities":
        if st.session_state.kg.entities:
            entities_df = pd.DataFrame([{
                "ID": e.id,
                "Type": e.type,
                "Name": e.name,
                "Confidence": e.confidence
            } for e in st.session_state.kg.entities])
            
            st.dataframe(entities_df)
            
            if st.button("Export Entities to CSV"):
                csv = entities_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="entities.csv",
                    mime="text/csv"
                )
        else:
            st.info("No entities found")

    elif data_type == "Relationships":
        if st.session_state.kg.relationships:
            entity_names = {e.id: e.name for e in st.session_state.kg.entities}
            
            relationships_df = pd.DataFrame([{
                "ID": r.id,
                "Type": r.type,
                "Source": entity_names.get(r.source, r.source),
                "Target": entity_names.get(r.target, r.target),
                "Confidence": r.confidence
            } for r in st.session_state.kg.relationships])
            
            st.dataframe(relationships_df)
            
            if st.button("Export Relationships to CSV"):
                csv = relationships_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="relationships.csv",
                    mime="text/csv"
                )
        else:
            st.info("No relationships found")

    else:
        if st.session_state.kg.text_chunks:
            chunks_df = pd.DataFrame([{
                "ID": c.id,
                "Text": c.text[:100] + "..." if len(c.text) > 100 else c.text,
                "Source": c.metadata.get("source", "Unknown")
            } for c in st.session_state.kg.text_chunks])
            
            st.dataframe(chunks_df)
            
            if st.button("Export Text Chunks to CSV"):
                csv = chunks_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="text_chunks.csv",
                    mime="text/csv"
                )
        else:
            st.info("No text chunks found")

    st.subheader("Clear Data")
    if st.button("Clear All Data", type="primary"):
        if st.session_state.kg.entities:
            st.session_state.kg.clear()
            st.session_state.loaded_files = []
            st.session_state.last_query = None
            st.session_state.last_result = None
            st.success("All data cleared")
            st.experimental_rerun()
        else:
            st.info("No data to clear")

