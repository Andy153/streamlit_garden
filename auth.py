"""Per-brand password authentication using st.secrets."""
from __future__ import annotations
import streamlit as st


def is_authenticated(brand_key: str) -> bool:
    return st.session_state.get(f"auth_{brand_key}", False)


def logout(brand_key: str) -> None:
    st.session_state[f"auth_{brand_key}"] = False


def show_login(brand_key: str, config: dict) -> None:
    """Render the login gate. Call st.stop() after this if not authenticated."""
    gradient = config["gradient"]
    title    = config["title"]

    st.html(f"""
    <div style="
        background: {gradient};
        padding: 18px 28px;
        border-radius: 10px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 18px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.25);
    ">
        <span style="color:white; font-size:26px; font-weight:900; letter-spacing:5px;
                     font-family:Inter,sans-serif;">{title.upper()}</span>
        <span style="color:rgba(255,255,255,0.35); font-size:22px; font-weight:200;">|</span>
        <div>
            <div style="color:white; font-size:17px; font-weight:600;
                        font-family:Inter,sans-serif; letter-spacing:0.3px;">Dashboard Gerencial</div>
            <div style="color:rgba(255,255,255,0.6); font-size:12px;
                        font-family:Inter,sans-serif; margin-top:2px;">Garden · Acceso restringido</div>
        </div>
    </div>
    """)

    col, _ = st.columns([1, 2])
    with col:
        st.markdown("#### :material/lock: Ingresá tu contraseña")
        with st.form(f"login_{brand_key}", clear_on_submit=True):
            pwd = st.text_input(
                "Contraseña",
                type="password",
                label_visibility="collapsed",
                placeholder="Contraseña",
            )
            submitted = st.form_submit_button("Ingresar →", use_container_width=True)

        if submitted:
            brand_passwords = st.secrets.get("brand_passwords", {})
            expected = brand_passwords.get(brand_key, "")
            if expected and pwd == expected:
                st.session_state[f"auth_{brand_key}"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta. Intentá de nuevo.")
