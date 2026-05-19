import streamlit as st
import requests
import pandas as pd
import re

# ---------------------- 页面配置 ----------------------
st.set_page_config(
    page_title="篇章分析综合平台",
    page_icon="📚",
    layout="wide"
)

# ---------------------- 模块1：话语分割（EDU切分） ----------------------
def simple_edu_segment(text):
    """基于规则的EDU切分（简化版）"""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    edus = []
    for sent in sentences:
        if not sent:
            continue
        splitters = [', ', ' but ', ' although ', ' because ', ' since ', ' and ', ' or ']
        segments = [sent]
        for splitter in splitters:
            new_segments = []
            for seg in segments:
                parts = seg.split(splitter)
                if len(parts) > 1:
                    new_segments.extend([parts[0] + splitter[:-1], splitter[1:] + parts[1]])
                else:
                    new_segments.append(seg)
            segments = new_segments
        edus.extend(segments)
    return edus

def get_neural_edu_sample():
    """获取NeuralEDUSeg的示例数据"""
    url = "https://raw.githubusercontent.com/PKU-TANGENT/NeuralEDUSeg/master/data/rst/test/wsj_0600.out"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.text
        else:
            return "The quick brown fox jumps over the lazy dog. Although it was tired, it kept running."
    except:
        return "The quick brown fox jumps over the lazy dog. Although it was tired, it kept running."

def parse_neural_edu_text(text):
    """解析NeuralEDUSeg格式文本"""
    lines = text.strip().split('\n')
    edus = []
    for line in lines[:10]:
        if line.strip():
            edus.append(line.strip())
    return edus

# ---------------------- 模块2：浅层篇章分析与显式关系提取 ----------------------
CONNECTIVES = {
    "Temporal": ["when", "after", "before", "while", "then"],
    "Contingency": ["because", "since", "as", "therefore", "thus"],
    "Comparison": ["but", "although", "however", "while", "whereas"],
    "Expansion": ["and", "or", "also", "moreover", "in addition"]
}

def extract_explicit_relations(text):
    """提取显式连接词及其关系"""
    relations = []
    text_lower = text.lower()
    for category, words in CONNECTIVES.items():
        for word in words:
            if word in text_lower:
                idx = text_lower.find(word)
                relations.append({
                    "connective": word,
                    "category": category,
                    "start": idx,
                    "end": idx + len(word)
                })
    return relations

def split_arguments(text, connective):
    """以连接词为界，分割Arg1和Arg2"""
    idx = text.lower().find(connective.lower())
    if idx == -1:
        return text, ""
    arg1 = text[:idx].strip()
    arg2 = text[idx + len(connective):].strip()
    return arg1, arg2

# ---------------------- 模块3：指代消解可视化（纯Python实现） ----------------------
def simple_coref_resolution(text):
    """简化版指代消解，仅处理he/she/it/they"""
    pronouns = ["he", "she", "it", "they", "his", "her", "its", "their"]
    # 提取文本中的实体（简单名词识别）
    words = text.split()
    entities = []
    for i, word in enumerate(words):
        if word[0].isupper() and word.lower() not in ["the", "and", "of", "to", "in"]:
            entities.append((word, i))
    
    pronouns_found = []
    for i, word in enumerate(words):
        if word.lower() in pronouns:
            pronouns_found.append((word, i))
    
    # 简单配对：代词指向最近的实体
    clusters = []
    for pronoun, p_idx in pronouns_found:
        best_entity = None
        min_dist = float('inf')
        for entity, e_idx in entities:
            if e_idx < p_idx:
                dist = p_idx - e_idx
                if dist < min_dist:
                    min_dist = dist
                    best_entity = entity
        if best_entity:
            clusters.append({
                "entity": best_entity,
                "mentions": [(best_entity, entities[0][1]), (pronoun, p_idx)]
            })
    return clusters

# ---------------------- 页面内容 ----------------------
st.title("📚 篇章分析综合平台")
st.markdown("---")

tab1, tab2, tab3 = st.tabs([
    "模块1：话语分割（EDU切分）",
    "模块2：浅层篇章分析与显式关系提取",
    "模块3：指代消解可视化"
])

# ---------------------- 模块1：话语分割 ----------------------
with tab1:
    st.header("✂️ 话语分割（EDU切分）")
    st.markdown("对比规则基线与真实数据的EDU切分结果")
    
    with st.spinner("加载示例数据..."):
        neural_text = get_neural_edu_sample()
        neural_edus = parse_neural_edu_text(neural_text)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("规则基线切分结果")
        input_text = st.text_area("输入文本进行切分", value="The quick brown fox jumps over the lazy dog. Although it was tired, it kept running.", height=150, key="edu_input")
        if st.button("规则切分", key="edu_btn"):
            rule_edus = simple_edu_segment(input_text)
            for i, edu in enumerate(rule_edus):
                st.markdown(f"**EDU {i+1}**: `{edu}`")
    
    with col2:
        st.subheader("NeuralEDUSeg示例结果")
        for i, edu in enumerate(neural_edus):
            st.markdown(f"**EDU {i+1}**: `{edu}`")

# ---------------------- 模块2：浅层篇章分析 ----------------------
with tab2:
    st.header("🔗 浅层篇章分析与显式关系提取")
    st.markdown("提取文本中的显式连接词，并分割前后论点")
    
    example_text = "Third-quarter sales in Europe were exceptionally strong, boosted by promotional programs and new products - although weaker foreign currencies reduced the company's earnings."
    input_text = st.text_area("输入文本进行分析", value=example_text, height=150, key="relation_input")
    
    if st.button("分析关系", key="relation_btn"):
        relations = extract_explicit_relations(input_text)
        if relations:
            st.subheader("识别到的连接词")
            for rel in relations:
                st.markdown(f"- `{rel['connective']}` ({rel['category']}) at position {rel['start']}-{rel['end']}")
                arg1, arg2 = split_arguments(input_text, rel['connective'])
                st.markdown(f"  - **Arg1**: `{arg1}`")
                st.markdown(f"  - **Arg2**: `{arg2}`")
        else:
            st.info("未识别到显式连接词")

# ---------------------- 模块3：指代消解可视化 ----------------------
with tab3:
    st.header("👥 指代消解可视化")
    st.markdown("识别文本中的代词，并高亮显示其指代的实体")
    
    example_text = "Barack Obama was born in Hawaii. He served as the 44th President of the United States. He was inaugurated in 2009."
    input_text = st.text_area("输入文本进行分析", value=example_text, height=150, key="coref_input")
    
    if st.button("消解指代", key="coref_btn"):
        clusters = simple_coref_resolution(input_text)
        if clusters:
            st.subheader("指代簇")
            for cluster in clusters:
                st.markdown(f"**实体**: {cluster['entity']}")
                for mention, idx in cluster['mentions']:
                    st.markdown(f"  - `{mention}` at index {idx}")
            
            # 简单高亮显示（用HTML）
            st.subheader("高亮文本")
            highlighted_text = input_text
            colors = ["#FFB3BA", "#BAFFC9", "#BAE1FF"]
            for i, cluster in enumerate(clusters):
                color = colors[i % len(colors)]
                entity, e_idx = cluster['mentions'][0]
                pronoun, p_idx = cluster['mentions'][1]
                highlighted_text = highlighted_text.replace(entity, f'<mark style="background-color: {color};">{entity}</mark>')
                highlighted_text = highlighted_text.replace(pronoun, f'<mark style="background-color: {color};">{pronoun}</mark>')
            st.markdown(highlighted_text, unsafe_allow_html=True)
        else:
            st.info("未识别到指代关系")

# ---------------------- 页脚 ----------------------
st.markdown("---")
st.markdown("© 2025 NLP 课程实验 | 篇章分析综合平台")
