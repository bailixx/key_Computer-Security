import streamlit as st
import hashlib
import base64
import json
import os
import logging
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes

# 强制绑定当前目录，防止幽灵文件
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(BASE_DIR, "my_passwords.json")
L = os.path.join(BASE_DIR, "sys.log")

# 配置日志
logging.basicConfig(filename=L, level=logging.INFO, format='%(asctime)s - %(message)s')

class K:
    def __init__(self):
        self.h = None   
        self.c = None   
        self.d = {}     
        self.x = None   # 私钥
        self.y = None   # 公钥
        self.o()

    def g(self, m):
        """日志记录"""
        logging.info(m)

    def n(self):
        """生成随机数"""
        r = secrets.token_hex(32)
        self.g(f"系统生成高强度随机密钥: {r}")
        return r

    def b(self):
        """生成RSA公私钥对"""
        self.x = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.y = self.x.public_key()
        self.g("系统成功生成了 RSA 非对称公私钥对")
        return True

    def i(self, t):
        """签名与验证"""
        if self.x is None:
            return False, "请先生成RSA密钥对！"
        try:
            # 签名
            s = self.x.sign(
                t.encode('utf-8'),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
            self.g(f"对数据 '{t}' 进行了数字签名")
            # 验证
            self.y.verify(
                s,
                t.encode('utf-8'),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
            self.g("数字签名验证成功")
            return True, "✅ 验证通过！证明数据确实是您签发且未被篡改。"
        except Exception:
            self.g("数字签名验证失败警告！")
            return False, "❌ 验证失败！数据伪造或已被篡改。"

    def f1(self, t):
        m = hashlib.md5()
        m.update(t.encode('utf-8'))
        return m.hexdigest()

    def f2(self, p):
        s = self.f1(p)
        return base64.urlsafe_b64encode(s.encode('utf-8'))

    def r(self, p):
        self.h = self.f1(p)
        self.c = Fernet(self.f2(p))
        self.s()
        self.g("首次运行，用户成功注册了系统主密码")

    def l(self, p):
        if self.f1(p) == self.h:
            self.c = Fernet(self.f2(p))
            self.g("用户通过主密码成功解锁了系统")
            return True
        self.g("警告：尝试登录失败，主密码错误")
        return False

    def a(self, w, u, p):
        e = self.c.encrypt(p.encode('utf-8')).decode('utf-8')
        self.d[w] = {"u": u, "e": e}
        self.s()
        self.g(f"添加并加密了新的网站记录: [{w}]")

    def q(self, w):
        if w in self.d:
            self.g(f"用户查询了网站记录: [{w}]")
            return self.d[w]["u"], self.c.decrypt(self.d[w]["e"].encode('utf-8')).decode('utf-8')
        return None

    def s(self):
        with open(F, 'w') as f:
            json.dump({"h": self.h, "d": self.d}, f, indent=4)

    def o(self):
        if os.path.exists(F):
            with open(F, 'r') as f:
                v = json.load(f)
                self.h = v.get("h")
                self.d = v.get("d", {})

# ================= Streamlit 网页交互 =================
st.set_page_config(page_title="安全密钥管理系统", page_icon="🔐", layout="centered")
st.title("🔐 安全密钥管理系统")

# 状态机初始化
if "m" not in st.session_state:
    st.session_state.m = K()
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "search_res" not in st.session_state:
    st.session_state.search_res = None

m = st.session_state.m

# ---- 登录与初始化流程 ----
if m.h is None:
    st.subheader("🆕 系统首次运行，请初始化")
    p1 = st.text_input("设置主密码:", type="password")
    p2 = st.text_input("确认主密码:", type="password")
    if st.button("完成初始化"):
        if p1 and p1 == p2:
            m.r(p1)
            st.success("初始化成功！请刷新页面。")
            st.rerun()
        else:
            st.error("密码不一致或为空！")

elif not st.session_state.logged_in:
    st.subheader("🔑 账户登录")
    p = st.text_input("输入主密码解锁:", type="password")
    if st.button("登录"):
        if m.l(p):
            st.session_state.logged_in = True
            st.success("解锁成功！")
            st.rerun()
        else:
            st.error("密码错误！")

# ---- 主界面 ----
else:
    st.sidebar.success("🔒 系统已解锁")
    if st.sidebar.button("安全退出"):
        st.session_state.logged_in = False
        st.session_state.search_res = None
        m.g("用户安全退出系统")
        st.rerun()
        
    t1, t2, t3, t4, t5 = st.tabs(["➕ 添加", "🔍 查询", "🎲 随机数", "🔏 签名", "📁 存储与日志"])
    
    with t1:
        st.subheader("添加密码记录")
        with st.form("add_form", clear_on_submit=True):
            w = st.text_input("网站名称:")
            u = st.text_input("登录账号:")
            p = st.text_input("登录密码:", type="password")
            if st.form_submit_button("加密保存"):
                if w and u and p:
                    if len(p) < 6:
                        st.warning("⚠️ 警告：该密码长度小于6位，安全性较弱！")
                        m.g(f"警告: 用户添加了弱密码 [{w}]")
                    m.a(w, u, p)
                    st.success(f"【{w}】已通过派生对称密钥加密保存！")
                else:
                    st.error("请填写完整！")
                    
    with t2:
        st.subheader("查询密码记录")
        if st.session_state.search_res is None:
            w = st.text_input("要查询的网站名称:")
            if st.button("查询"):
                res = m.q(w)
                if res:
                    st.session_state.search_res = {"w": w, "u": res[0], "p": res[1]}
                    st.rerun()
                else:
                    st.error("未找到记录！")
        else:
            r = st.session_state.search_res
            st.info(f"**网站**: {r['w']} \n\n **账号**: {r['u']}")
            st.code(r['p'], language="text")
            if st.button("↩️ 隐藏并返回"):
                st.session_state.search_res = None
                st.rerun()
                
    with t3:
        st.subheader("生成安全随机数")
        st.write("调用系统底层熵池生成不可预测的 32 字节随机密钥。")
        if st.button("生成随机密钥"):
            st.code(m.n(), language="text")
            
    with t4:
        st.subheader("RSA 非对称密钥对与数字签名")
        if st.button("1. 生成 RSA 公私钥对"):
            m.b()
            st.success("RSA 2048位公私钥对已生成并驻留内存！")
            
        t = st.text_input("输入需要进行数字签名的防篡改内容:")
        if st.button("2. 执行签名与验证"):
            ok, msg = m.i(t)
            if ok:
                st.success(msg)
            else:
                st.error(msg)
                
    with t5:
        st.subheader("数据与审计日志监控")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("📦 数据库密文 (JSON)")
            if os.path.exists(F):
                with open(F, 'r') as f:
                    st.json(json.load(f))
        with c2:
            st.markdown("📜 审计日志 (sys.log)")
            if os.path.exists(L):
                with open(L, 'r', encoding='utf-8') as f:
                    st.text(f.read())
            else:
                st.write("暂无日志")