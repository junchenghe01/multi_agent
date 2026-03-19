import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# 1. 静态配置层
from configs.settings import settings

# 2. 指令资产层
from prompts.loader import PromptLoader

# 3. 智能体逻辑层
from agents.factory import AgentFactory

# 4. 状态与编排层
from core.engine import WorkflowEngine
from core.schema import InitialState

def setup_environment():
    """初始化环境与日志"""
    load_dotenv()
    # 确保日志目录存在
    settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    (settings.LOGS_DIR / "thoughts").mkdir(parents=True, exist_ok=True)
    print("[System] Environment initialized.")

def main():
    # --- Step 1: 环境与配置加载 ---
    setup_environment()
    
    # --- Step 2: 加载 Markdown 指令资产 ---
    print("[System] Loading prompt assets from Markdown...")
    # 注意：我们的 PromptLoader 内部已经关联了 settings.PROMPTS_DIR
    prompt_assets = PromptLoader.load_all() # TODO: 未使用
    
    # --- Step 3: 组装 Agent 实例 ---
    print("[System] Assembling agents via Factory...")
    # 修改：AgentFactory 内部会读取 agents.yaml，不需要重复传参
    agent_factory = AgentFactory()
    
    # 修改：方法名从 create_role 改为 create_agent 以对齐 factory.py
    agents_pool = {
        "boss": agent_factory.create_agent("boss"),
        "coder": agent_factory.create_agent("coder"),
        "reviewer": agent_factory.create_agent("reviewer")
    } # TODO: 未使用

    # --- Step 4: 构建编排引擎 ---
    print("[System] Initializing workflow engine...")
    # 修改：确保 WorkflowEngine 接收的是初始化好的 agents 字典
    engine = WorkflowEngine()  # TODO: 这里又加载了智能体
    # 如果你的 engine 内部已经自己创建了 agent，这里甚至不需要传参
    # 如果需要传参，请确保 engine.__init__ 支持：engine = WorkflowEngine(agents=agents_pool)
    app = engine.compile()

    # --- Step 5: 启动任务 ---
    user_input = input("\n请输入您的任务指令: ")
    
    # 构造符合 core/schema.py 中 AgentState 要求的初始状态字典
    # 因为 LangGraph 运行的是字典状态
    initial_state_dict = {
        "messages": [HumanMessage(content=user_input)],
        "next_step": "boss",
        "metadata": {"task": user_input},
        "session_id": "session_001"
    }

    print(f"\n{'='*20} 任务开始 {'='*20}")
    # 使用 stream 模式运行 LangGraph
    for event in app.stream(initial_state_dict):
        for node_name, state_update in event.items():
            print(f"\n[Node: {node_name}]")
            if "messages" in state_update and state_update["messages"]:
                last_msg = state_update["messages"][-1]
                # 打印内容前 100 个字符
                print(f"Content: {last_msg.content[:100]}...")
    
    print(f"\n{'='*20} 任务完成 {'='*20}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[System] Process interrupted by user.")
    except Exception as e:
        print(f"\n[Error] Critical failure: {e}")
        # 打印详细错误追踪，方便调试
        import traceback
        traceback.print_exc()
