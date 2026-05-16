import streamlit as st
import hashlib
import base64
import json
import os
from cryptography.fernet import Fernet

# 强制将数据文件绑定在代码所在的目录下
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "my_passwords.json")

# ================= 核心安全类 (保留原有逻辑) =================
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

# ================= Streamlit 网页渲染页面 =================
st.set_page_config(page_title="安全密钥管理系统", page_icon="🔐", layout="centered")
st.title("🔐 基于 MD5 的安全密钥管理系统")

# 使用 Streamlit 缓存机制，防止页面每次刷新都重新实例化类
if "manager" not in st.session_state:
    st.session_state.manager = KeyManager()
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

manager = st.session_state.manager

# 判断是否需要初始化主密码
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

# 如果已经有主密码，且尚未登录
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

# 登录成功后的主操作界面
else:
    st.sidebar.success("🔒 数据库已解锁")
    if st.sidebar.button("安全退出登录"):
        st.session_state.logged_in = False
        st.rerun()
        
    # 网页标签页布局
    tab1, tab2, tab3 = st.tabs(["➕ 添加账号密码", "🔍 查询账号密码", "📁 查看数据库底层密文"])
    
    with tab1:
        st.subheader("添加新网站的账号密码")
        site = st.text_input("请输入网站/应用名称 (例如: 淘宝、Github):")
        account = st.text_input("请输入登录账号:")
        password = st.text_input("请输入登录密码:", type="password")
        
        if st.button("加密保存记录"):
            if site and account and password:
                # 强度检测
                if len(password) < 6:
                    st.warning("⚠️ 警告：该密码长度小于 6 位，安全性较低！")
                
                manager.add_password(site, account, password)
                st.success(f"【{site}】的密码已成功通过主密码派生密钥加密存入本地文件！")
            else:
                st.error("所有字段均不能为空！")
                
    with tab2:
        st.subheader("查询已保存的密码")
        search_site = st.text_input("请输入要查询的网站/应用名称:")
        if st.button("点击查询解密"):
            if search_site:
                result = manager.get_password(search_site)
                if result:
                    acc, pwd = result
                    st.info(f"**查询网站**：{search_site}")
                    st.info(f"**登录账号**：{acc}")
                    st.code(f"{pwd}", language="text") # 用代码块展示密码，方便复制
                else:
                    st.error("未找到该网站的加密记录！")
            else:
                st.error("请输入要查询的网站名称！")
                
    with tab3:
        st.subheader("📦 本地硬盘 JSON 存储状态 (零知识证明技术展示)")
        st.write("这是黑客如果偷走你的文件，在不带主密码的情况下能看到的真实内容：")
        
        # 实时读取磁盘文件并展示
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                raw_json = json.load(f)
            st.json(raw_json)
        else:
            st.write("暂无数据。")