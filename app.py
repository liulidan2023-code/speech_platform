import os
import asyncio
import edge_tts
from datetime import datetime

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import session
from flask import send_from_directory

# =========================
# Flask
# =========================

app = Flask(__name__)
app.secret_key = "hanyu_reading_platform"

# =========================
# 教师账号
# =========================

TEACHER_USERNAME = "admin"
TEACHER_PASSWORD = "123456"

# =========================
# 路径配置
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEACHER_AUDIO = os.path.join(
    BASE_DIR,
    "static",
    "teacher_audio"
)

STUDENT_AUDIO = os.path.join(
    BASE_DIR,
    "static",
    "student_audio"
)

CLASS_FILE = os.path.join(
    BASE_DIR,
    "classes.txt"
)

os.makedirs(
    TEACHER_AUDIO,
    exist_ok=True
)

os.makedirs(
    STUDENT_AUDIO,
    exist_ok=True
)

if not os.path.exists(CLASS_FILE):

    with open(
        CLASS_FILE,
        "w",
        encoding="utf-8"
    ):
        pass


# =========================
# 班级管理
# =========================

def load_classes():

    if not os.path.exists(CLASS_FILE):
        return []

    with open(
        CLASS_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return [
            line.strip()
            for line in f
            if line.strip()
        ]


def save_class(class_name):

    class_name = class_name.strip()

    if not class_name:
        return

    classes = load_classes()

    if class_name not in classes:

        with open(
            CLASS_FILE,
            "a",
            encoding="utf-8"
        ) as f:

            f.write(class_name + "\n")


# =========================
# 首页（学生入口）
# =========================

@app.route("/")
def index():

    classes = load_classes()

    return render_template(
        "upload.html",
        classes=classes
    )


# =========================
# 登录
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if (
            username == TEACHER_USERNAME
            and password == TEACHER_PASSWORD
        ):

            session["teacher"] = True

            return redirect("/teacher_home")

    return render_template("login.html")


# =========================
# 退出
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================
# 教师中心
# =========================

@app.route("/teacher_home")
def teacher_home():

    if not session.get("teacher"):
        return redirect("/login")

    return render_template(
        "teacher_home.html"
    )


# =========================
# TTS生成录音
# =========================

@app.route("/generate", methods=["GET", "POST"])
def generate():

    if not session.get("teacher"):
        return redirect("/login")

    if request.method == "POST":

        try:

            text = request.form["text"]

            output_path = os.path.join(
                TEACHER_AUDIO,
                "teacher.mp3"
            )

            asyncio.run(
                create_tts(
                    text,
                    output_path
                )
            )

            return """
            <h2>录音生成成功！</h2>
            <a href='/teacher_home'>
            返回教师中心
            </a>
            """

        except Exception as e:

            return f"""
            <h2>录音生成失败</h2>
            <pre>{str(e)}</pre>
            """

    return render_template(
        "generate.html"
    )


async def create_tts(
    text,
    output_path
):

    communicate = edge_tts.Communicate(
        text=text,
        voice="zh-CN-XiaoxiaoNeural"
    )

    await communicate.save(
        output_path
    )


# =========================
# 班级管理
# =========================

@app.route(
    "/class_manage",
    methods=["GET", "POST"]
)
def class_manage():

    if not session.get("teacher"):
        return redirect("/login")

    if request.method == "POST":

        class_name = request.form[
            "class_name"
        ]

        save_class(class_name)

        return redirect(
            "/class_manage"
        )

    return render_template(
        "class_manage.html",
        classes=load_classes()
    )


# =========================
# 学生上传
# =========================

@app.route(
    "/upload",
    methods=["GET", "POST"]
)
def upload():

    classes = load_classes()

    if request.method == "POST":

        class_name = request.form[
            "class_name"
        ]

        student_name = request.form[
            "student_name"
        ]

        audio = request.files[
            "audio"
        ]

        if audio:

            class_folder = os.path.join(
                STUDENT_AUDIO,
                class_name
            )

            os.makedirs(
                class_folder,
                exist_ok=True
            )

            ext = os.path.splitext(
                audio.filename
            )[1]

            timestamp = datetime.now().strftime(
                "%Y%m%d%H%M%S"
            )

            filename = (
                f"{student_name}_{timestamp}{ext}"
            )

            save_path = os.path.join(
                class_folder,
                filename
            )

            audio.save(save_path)

            return """
            <h2>上传成功！</h2>
            <br>
            <a href='/'>
            返回上传页面
            </a>
            """

    return render_template(
        "upload.html",
        classes=classes
    )


# =========================
# 教师查看作业
# =========================

@app.route("/teacher")
def teacher():

    if not session.get("teacher"):
        return redirect("/login")

    result = {}

    for class_name in load_classes():

        class_folder = os.path.join(
            STUDENT_AUDIO,
            class_name
        )

        if os.path.exists(
            class_folder
        ):

            result[class_name] = sorted(
                os.listdir(
                    class_folder
                )
            )

        else:

            result[class_name] = []

    return render_template(
        "teacher.html",
        data=result
    )


# =========================
# 下载录音
# =========================

@app.route(
    "/download/<class_name>/<filename>"
)
def download_audio(
    class_name,
    filename
):

    if not session.get("teacher"):
        return redirect("/login")

    folder = os.path.join(
        STUDENT_AUDIO,
        class_name
    )

    return send_from_directory(
        folder,
        filename,
        as_attachment=True
    )


# =========================
# 启动
# =========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )