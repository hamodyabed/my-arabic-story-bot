import streamlit as st
from audio_recorder_streamlit import audio_recorder
import os
import google.generativeai as genai

# إعداد مفتاح API (تأكد من استخدام مفتاحك الخاص)
os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
# ملاحظة: إذا لم يعمل gemini-2.5-flash، جرب gemini-1.5-flash أو الموديلات المتاحة في حسابك
model = genai.GenerativeModel('gemini-2.5-flash')

# إعدادات الصفحة والتصميم العربي
st.set_page_config(page_title="بوت قصص الأطفال الذكي", layout="centered")
st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; }
    div.stButton > button { width: 100%; border-radius: 20px; background-color: #4CAF50; color: white; font-weight: bold; }
    .stTextArea textarea { direction: rtl; }
    .stTextInput input { direction: rtl; }
    .question-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-right: 5px solid #4CAF50; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 بوت القصص والتحليل الذكي")

# إدارة الذاكرة (Session State)
if 'story' not in st.session_state:
    st.session_state['story'] = ""
if 'questions' not in st.session_state:
    st.session_state['questions'] = []

tab1, tab2 = st.tabs(["👩‍🏫 إعداد المعلمة", "👶 إجابة الطفل"])

# --- الجزء الأول: واجهة المعلمة ---
with tab1:
    st.header("إعداد القصة والأسئلة")
    story_content = st.text_area("أدخلي نص القصة:", value=st.session_state['story'], height=150)

    st.subheader("الأسئلة حول القصة")
    q1 = st.text_input("السؤال الأول:", placeholder="مثلاً: ماذا فعل الأرنب؟")
    q2 = st.text_input("السؤال الثاني:", placeholder="مثلاً: من ساعد الأرنب؟")

    if st.button("حفظ القصة والأسئلة"):
        st.session_state['story'] = story_content
        st.session_state['questions'] = [q for q in [q1, q2] if q]  # حفظ الأسئلة غير الفارغة
        st.success("تم الحفظ بنجاح! يمكنك الآن الانتقال لواجعة الطفل.")

# --- الجزء الثاني: واجهة الطفل والتحليل ---
with tab2:
    if not st.session_state['story'] or not st.session_state['questions']:
        st.warning("يرجى إدخال القصة والأسئلة أولاً في واجهة المعلمة.")
    else:
        st.header("وقت الإجابة")
        st.info("القصة: " + st.session_state['story'][:50] + "...")

        # عرض الأسئلة واحد تلو الآخر
        for i, question in enumerate(st.session_state['questions']):
            st.markdown(f"<div class='question-box'><b>السؤال {i + 1}:</b> {question}</div>", unsafe_allow_html=True)

            # تسجيل صوتي لكل سؤال بشكل منفصل
            st.write(f"سجل إجابتك على السؤال {i + 1}:")
            audio_bytes = audio_recorder(key=f"audio_{i}", text="اضغط للتحدث", icon_size="2x")

            if audio_bytes:
                st.audio(audio_bytes, format="audio/wav")

                if st.button(f"تحليل إجابة السؤال {i + 1}", key=f"btn_{i}"):
                    with st.spinner("جاري تحليل صوت الطفل وفهم الإجابة..."):
                        try:
                            audio_file = {"mime_type": "audio/wav", "data": audio_bytes}

                            prompt = f"""
                            أنت معلمة روضة خبيرة. 
                            القصة هي: {st.session_state['story']}
                            السؤال المطلوب من الطفل إجابته هو: {question}

                            بناءً على التسجيل الصوتي المرفق للطفل (عمره 4 سنوات):
                            1. قم بكتابة نص ما قاله الطفل بدقة.
                            2. حلل الإجابة: هل هي صحيحة أم خاطئة بناءً على القصة؟
                            3. قيم نبرة صوت الطفل (هل يبدو واثقاً، متردداً، فرحاً؟).
                            4. أعطِ درجة من 100.
                            5. اكتب رد فعل مشجع للطفل بصوت المعلمة.

                            أجب باللغة العربية الفصحى البسيطة وبشكل منظم.
                            """

                            response = model.generate_content([prompt, audio_file])
                            st.subheader(f"تحليل السؤال {i + 1}:")
                            st.markdown(response.text)
                            st.divider()

                        except Exception as e:
                            st.error(f"حدث خطأ أثناء التحليل: {e}")
