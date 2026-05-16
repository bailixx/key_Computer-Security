import streamlit as st
import hashlib
import base64
import json
import os
from cryptography.fernet import Fernet

# 强制将数据文件绑定在代码所在的目录下
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "my_passwords.json")

# ================= 核心安全类 (保留原有密码学逻辑) =================
class KeyManager:
    def __init__(self):
        self.master_hash = None
        self.cipher_suite = None
        self.passwords_db = {}
        self.load_data()

    def _get_md5(self, text):
        md5 = hashlib.md5()
        md5.update(text.encode('utf-8'))
        return md5.hexdigest()

    def _generate_key_from_password(self, password):
        md5_str = self._get_md5(password)
        key = base64.urlsafe_b64encode(md5_str.encode('utf-8'))
        return key

    def register_master_password(self, password):
        self.master_hash = self._get_md5(password)
        key = self._generate_key_from_password(password)
        self.cipher_suite = Fernet(key)
        self.save_data()

    def verify_and_init(self, password):
        if self._get_md5(password) == self.master_hash:
            key = self._generate_key_from_password(password)
            self.cipher_suite = Fernet(key)
            return True
        return False

    def add_password(self, website, account, pwd):
        encrypted_pwd = self.cipher_suite.encrypt(pwd.encode('utf-8')).decode('utf-8')
        self.passwords_db[website] = {
            "account": account,
            "encrypted_password": encrypted_pwd
        }
        self.save_data()

    def get_password(self, website):
        if website in self.passwords_db:
            data = self.passwords_db[website]
            encrypted_pwd = data["encrypted_password"]
            decrypted_pwd = self.cipher_suite.decrypt(encrypted_pwd.encode('utf-8')).decode('utf-8')
            return data["account"], decrypted_pwd
        return None

    def save_data(self):
        data = {
            "master_hash": self.master_hash,
            "passwords_db": self.passwords_db
        }
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                self.master_hash = data.get("master_hash")
                self.passwords_db = data.get("passwords_db", {})

# ================= Streamlit 网页渲染与交互升级 =================
st.set_page_config(page_title="安全密钥管理系统", page_icon="🔐", layout="centered")
st.title("🔐 基于 MD5 的安全密钥管理系统")

# 1. 初始化系统状态变量（新增：查询结果状态机）
if "manager" not in st.session_state:
    st.session_state.manager = KeyManager()
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_search_result" not in st.session_state:
    st.session_state.current_search_result = None  # 用来存放当前的查询结果

manager = st.session_state.manager

# ---- 登录与初始化验证流程 ----
if manager.master_hash is None:
    st.subheader("🆕 系统首次运行，请初始化主密码")
    new_pwd = st.text_input("请设置您的大师级主密码 (Master Password):", type="password")
    confirm_pwd = st.text_input("请再次输入主密码以确认:", type="password")
    
    if st.button("完成系统初始化"):
        if new_pwd and new_pwd == confirm_pwd:
            manager.register_master_password(new_pwd)
            st.success("系统初始化成功！请刷新页面或开始登录。")
            st.rerun()
        else:
            st.error("两次输入的密码不一致，或密码不能为空！")

elif not st.session_state.logged_in:
    st.subheader("🔑 账户登录")
    login_pwd = st.text_input("请输入主密码以解锁数据库:", type="password")
    
    if st.button("登录解锁"):
        if manager.verify_and_init(login_pwd):
            st.session_state.logged_in = True
            st.success("解锁成功！欢迎进入系统。")
            st.rerun()
        else:
            st.error("主密码错误，身份验证失败！")

# ---- 登录成功后的主操作菜单 ----
else:
    st.sidebar.success("🔒 数据库已解锁")
    if st.sidebar.button("安全退出登录"):
        st.session_state.logged_in = False
        st.session_state.current_search_result = None
        st.rerun()
        
    tab1, tab2, tab3 = st.tabs(["➕ 添加账号密码", "🔍 查询账号密码", "📁 查看数据库底层密文"])
    
    # ---------------- TAB 1: 添加页面 (引入表单机制，防止输入残留) ----------------
    with tab1:
        st.subheader("添加新网站的账号密码")
        with st.form("add_password_form", clear_on_submit=True):
            site = st.text_input("请输入网站/应用名称 (例如: 淘宝、Github):")
            account = st.text_input("请输入登录账号:")
            password = st.text_input("请输入登录密码:", type="password")
            #  这是修正后的正确代码
            submit_btn = st.form_submit_button("加密保存记录")
            
        if submit_btn:
            if site and account and password:
                if len(password) < 6:
                    st.warning("⚠️ 警告：该密码长度小于 6 位，安全性较低！")
                
                manager.add_password(site, account, password)
                st.success(f"成功！【{site}】的明文密码已通过对称算法完成加密落盘！")
                # 提示用户可以点击下方按钮返回或继续
                st.info("💡 输入框已自动清空。您可以继续添加，或点击其他标签页。")
            else:
                st.error("所有字段均不能为空！")
                
    # ---------------- TAB 2: 查询页面 (新增完美返回/隐藏密码功能) ----------------
    with tab2:
        st.subheader("查询已保存的密码")
        
        # 只有在没有展示查询结果时，才显示输入框和查询按钮
        if st.session_state.current_search_result is None:
            search_site = st.text_input("请输入要查询的网站/应用名称:")
            if st.button("点击查询解密"):
                if search_site:
                    result = manager.get_password(search_site)
                    if result:
                        # 将查询结果存入状态机，锁死在网页上
                        st.session_state.current_search_result = {
                            "site": search_site,
                            "account": result[0],
                            "pwd": result[1]
                        }
                        st.rerun()
                    else:
                        st.error("未找到该网站的加密记录！")
                else:
                    st.error("请输入要查询的网站名称！")
        
        # 如果状态机里有查询结果，渲染结果页面，并提供“返回”按钮
        else:
            res = st.session_state.current_search_result
            st.info(f"**查询网站**：{res['site']}")
            st.info(f"**登录账号**：{res['account']}")
            st.code(f"{res['pwd']}", language="text")
            
            # 【核心新增功能】：返回按钮
            if st.button("↩️ 隐藏密码并返回主菜单"):
                # 清空查询状态机
                st.session_state.current_search_result = None
                # 强行刷新网页，让页面彻底回到初始未查询状态
                st.rerun()
                
    # ---------------- TAB 3: 密文查看 ----------------
    with tab3:
        st.subheader("📦 本地硬盘 JSON 存储状态 (零知识证明技术展示)")
        st.write("这是黑客如果偷走你的文件，在不带主密码的情况下能看到的真实内容：")
        
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                raw_json = json.load(f)
            st.json(raw_json)
        else:
            st.write("暂无数据。")