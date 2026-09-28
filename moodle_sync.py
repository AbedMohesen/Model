#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
أداة المزامنة التلقائية مع مودل الجامعة الإسلامية بغزة (IUG Moodle Sync)
المقررات: نظم تشغيل • اتصالات بيانات • تنظيم حاسوب ولغة أسمبلي
=============================================================================
الوظيفة:
1. تسجيل الدخول الآمن إلى مودل الجامعة عبر بوابة المصادقة الموحدة (SSO)
2. فحص المواد الدراسية المسجلة وتحديد أي محاضرات أو سلايدات أو فيديوهات جديدة
3. تنزيل الملفات الجديدة وتنظيف أسمائها تلقائياً
4. تحديث قاعدة بيانات الموقع (data.js) وصفحات المقررات
5. الرفع التلقائي (Git Push) إلى المستودع والاستضافة مباشرة
"""

import os
import sys
import re
import json
import urllib.parse
import subprocess
import argparse
from pathlib import Path

# ضبط مخرجات الطرفية في ويندوز لدعم العربية والرموز بدون أخطاء ترميز
if sys.platform.startswith("win"):
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    import requests
except ImportError:
    print("❌ تنبيه: مكتبة requests غير مثبتة. قم بتثبيتها عبر: pip install requests")
    sys.exit(1)

# إعداد المسارات الأساسية
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
DATA_JS_PATH = BASE_DIR / "data.js"

# خريطة المقررات المعتمدة في البوابة
KNOWN_COURSES = [
    {
        "id": "os",
        "moodle_id": 12297,
        "keywords": ["نظم تشغيل", "operating systems", "ecom4401"],
        "folder": "OS",
        "page": "course-os.html",
        "title": "نظم تشغيل"
    },
    {
        "id": "data_comm",
        "moodle_id": 4455,
        "keywords": ["اتصالات بيانات", "data communication", "data communications", "ecom4411"],
        "folder": "DataCom",
        "page": "course-datacom.html",
        "title": "اتصالات بيانات"
    },
    {
        "id": "assembly",
        "moodle_id": 2463,
        "keywords": ["تنظيم حاسوب", "أسمبلي", "تجميع", "assembly", "ecom4403", "ecom4412"],
        "folder": "Assembly",
        "page": "course-assembly.html",
        "title": "تنظيم حاسوب ولغة أسمبلي"
    }
]


def load_env(env_file=ENV_PATH):
    """قراءة متغيرات البيئة من ملف .env"""
    env_vars = {}
    if not env_file.exists():
        return env_vars

    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                env_vars[key.strip()] = val.strip().strip("\"'")
    return env_vars


class IUGMoodleSync:
    BASE_URL = "https://moodle.iugaza.edu.ps"
    SAML_URL = "https://moodle.iugaza.edu.ps/auth/saml2/login.php?wants&idp=907e0c01dccba9d62ae57512cec18ed8&passive=off"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})
        self.is_logged_in = False
        self.sesskey = None
        self.user_fullname = ""

    def login(self):
        """تسجيل الدخول إلى مودل الجامعة عبر بوابة المصادقة الموحدة (SSO)"""
        print("🔄 جاري الاتصال ببوابة المصادقة الموحدة (sso.iugaza.edu.ps)...")
        try:
            r_sso = self.session.get(self.SAML_URL, allow_redirects=True, timeout=25)
            auth_match = re.search(r'AuthState=([^&]+)', r_sso.url)
            if not auth_match:
                print("❌ تعذر العثور على رمز الجلسة AuthState من صفحة SSO.")
                return False

            auth_state = urllib.parse.unquote(auth_match.group(1))
            login_res = self.session.post(
                r_sso.url,
                data={
                    "username": self.username,
                    "password": self.password,
                    "AuthState": auth_state
                },
                allow_redirects=True,
                timeout=25
            )

            # التحقق من وجود رسالة خطأ
            err = re.search(r'class=["\'][^"\']*alert[^"\']*["\'][^>]*>(.*?)</div>', login_res.text, re.DOTALL)
            if err:
                msg = re.sub(r'<[^>]+>', ' ', err.group(1)).strip()
                print(f"❌ خطأ من سيرفر الجامعة: {msg}")
                return False

            # إرسال استجابة SAMLResponse لمودل
            if 'name="SAMLResponse"' in login_res.text:
                saml_resp_match = re.search(r'name="SAMLResponse" value="([^"]+)"', login_res.text)
                saml_action_match = re.search(r'action="([^"]+)"', login_res.text)
                if saml_resp_match and saml_action_match:
                    action = saml_action_match.group(1)
                    resp_val = saml_resp_match.group(1)
                    dashboard = self.session.post(action, data={"SAMLResponse": resp_val}, allow_redirects=True, timeout=25)
                    return self._process_dashboard(dashboard.text)

            return self._process_dashboard(login_res.text)
        except Exception as e:
            print(f"❌ استثناء أثناء تسجيل الدخول: {e}")
            return False

    def _process_dashboard(self, html_text):
        """استخراج مفتاح الجلسة والتحقق من اكتمال الدخول"""
        sesskey_m = re.search(r'"sesskey":"([^"]+)"', html_text)
        if sesskey_m:
            self.sesskey = sesskey_m.group(1)
            self.is_logged_in = True
            
            # استخراج اسم الطالب
            name_m = re.search(r'class="usertext mr-1"[^>]*>([^<]+)<', html_text)
            if not name_m:
                name_m = re.search(r'"userfullname":"([^"]+)"', html_text)
            if name_m:
                self.user_fullname = name_m.group(1).strip()
                print(f"✅ مرحباً بك يا {self.user_fullname} (تم تسجيل الدخول بنجاح)")
            else:
                print("✅ تم تسجيل الدخول بنجاح إلى حساب الطالب!")
            return True
        return False

    def get_enrolled_courses(self):
        """جلب المقررات المسجلة للطالب عبر WebService API المدمج في المودل"""
        print("📚 جاري جلب قائمة المقررات الدراسية المعتمدة من حسابك...")
        courses = []
        
        # 1. محاولة الجلب عبر WebService API
        if self.sesskey:
            try:
                service_url = f"{self.BASE_URL}/lib/ajax/service.php?sesskey={self.sesskey}&info=core_course_get_enrolled_courses_by_timeline_classification"
                payload = [{
                    "index": 0,
                    "methodname": "core_course_get_enrolled_courses_by_timeline_classification",
                    "args": {"offset": 0, "limit": 0, "classification": "all", "sort": "fullname"}
                }]
                api_res = self.session.post(service_url, json=payload, timeout=25)
                if api_res.status_code == 200:
                    data = api_res.json()
                    moodle_courses = data[0].get("data", {}).get("courses", [])
                    for mc in moodle_courses:
                        cid = mc.get("id")
                        fullname = mc.get("fullname", "").strip()
                        shortname = mc.get("shortname", "").strip()
                        combined = f"{fullname} {shortname}".lower()

                        matched_info = None
                        for mapping in KNOWN_COURSES:
                            if mapping["moodle_id"] == cid or any(kw in combined for kw in mapping["keywords"]):
                                matched_info = mapping
                                break

                        courses.append({
                            "id": cid,
                            "url": f"{self.BASE_URL}/course/view.php?id={cid}",
                            "title": fullname,
                            "shortname": shortname,
                            "mapping": matched_info
                        })
            except Exception as e:
                print(f"⚠️ تنبيه أثناء استدعاء API المقررات: {e}")

        # 2. في حال عدم العثور عليها أو وجود خلل في API نعتمد المقررات الثابتة المؤكدة
        if not courses:
            for k in KNOWN_COURSES:
                courses.append({
                    "id": k["moodle_id"],
                    "url": f"{self.BASE_URL}/course/view.php?id={k['moodle_id']}",
                    "title": k["title"],
                    "shortname": k["id"],
                    "mapping": k
                })

        print(f"ℹ️ تم التعرف على {len(courses)} مقرراً دراسياً:")
        for c in courses:
            status_text = f"➡️ [مربوط مع صفحة: {c['mapping']['title']}]" if c['mapping'] else "(غير مشمول في البوابة)"
            print(f"   • {c['title']} (ID: {c['id']}) {status_text}")

        return courses

    def sync_course(self, course_info):
        """فحص وتنزيل محتويات المقرر المربوط وتحديث الروابط"""
        mapping = course_info["mapping"]
        if not mapping:
            return []

        folder_name = mapping["folder"]
        folder_path = BASE_DIR / folder_name
        folder_path.mkdir(exist_ok=True)

        print(f"\n🔍 جاري فحص مقرر: {mapping['title']} (مجلد: {folder_name}/)...")
        r = self.session.get(course_info["url"], timeout=25)
        
        # استخراج أنشطة المودل
        # 1. ملفات الموارد /mod/resource/
        resource_ids = set(re.findall(r'/mod/resource/view\.php\?id=(\d+)', r.text))
        
        # 2. روابط الفيديوهات والمحاضرات الخارجية /mod/url/
        url_ids = set(re.findall(r'/mod/url/view\.php\?id=(\d+)', r.text))

        downloaded_new_files = []

        # فحص وتنزيل الملفات المرفوعة
        for rid in resource_ids:
            res_url = f"{self.BASE_URL}/mod/resource/view.php?id={rid}"
            downloaded = self._download_file_if_new(res_url, folder_path)
            if downloaded:
                downloaded_new_files.append(downloaded)

        return downloaded_new_files

    def _download_file_if_new(self, url, target_dir):
        """تنزيل الملف في حال كان جديداً وغير مكرر"""
        try:
            head = self.session.head(url, allow_redirects=True, timeout=15)
            content_type = head.headers.get("Content-Type", "")
            content_disp = head.headers.get("Content-Disposition", "")
            
            if "text/html" in content_type:
                return None

            filename = None
            if "filename=" in content_disp:
                fn_match = re.search(r'filename\*?=(?:UTF-8\'\')?["\']?([^"\';]+)["\']?', content_disp)
                if fn_match:
                    filename = urllib.parse.unquote(fn_match.group(1))

            if not filename:
                filename = os.path.basename(urllib.parse.urlparse(head.url).path)

            if not filename or filename == "view.php":
                return None

            # تنظيف اسم الملف وحذف (1) و (2)
            clean_filename = self._clean_filename(filename)
            target_file = target_dir / clean_filename

            # التحقق إن كان الملف موجوداً مسبقاً بنفس الحجم
            content_length = int(head.headers.get("Content-Length", 0))
            if target_file.exists() and content_length > 0:
                if target_file.stat().st_size == content_length:
                    return None

            # تنزيل الملف
            print(f"   📥 تنزيل ملف جديد: {clean_filename} ...")
            resp = self.session.get(url, stream=True, timeout=40)
            with open(target_file, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)

            size_mb = round(target_file.stat().st_size / (1024 * 1024), 2)
            print(f"   ✅ تم حفظ: {clean_filename} ({size_mb} MB)")
            return {
                "filename": clean_filename,
                "relative_path": f"{target_dir.name}/{clean_filename}",
                "size_mb": size_mb,
                "folder": target_dir.name
            }
        except Exception as e:
            return None

    def _clean_filename(self, name):
        """تنظيف اسم الملف من لاحقات ويندوز المكررة والرموز المزعجة"""
        name = urllib.parse.unquote(name)
        name = re.sub(r'\s*\(\d+\)', '', name)
        name = name.strip()
        return name


def update_database_with_new_files(new_files):
    """إضافة أي ملفات جديدة تم تنزيلها إلى قاعدة بيانات data.js"""
    if not new_files or not DATA_JS_PATH.exists():
        return

    try:
        with open(DATA_JS_PATH, "r", encoding="utf-8") as f:
            data_text = f.read()

        added_count = 0
        for nf in new_files:
            rel_path = nf["relative_path"]
            if rel_path in data_text:
                continue

            folder = nf["folder"]
            filename = nf["filename"]
            ext = Path(filename).suffix.lower().replace(".", "")
            ftype = "ppt" if ext in ["ppt", "pptx"] else ("pdf" if ext == "pdf" else ("video" if ext in ["mp4", "webm"] else "doc"))
            item_title = Path(filename).stem
            course_id = "os" if folder == "OS" else ("data_comm" if folder == "DataCom" else "assembly")

            marker = f'id: "{course_id}"'
            idx = data_text.find(marker)
            if idx != -1:
                sec_bracket = data_text.find("sections: [", idx)
                if sec_bracket != -1:
                    new_section = f'''      {{
        title: "{item_title}",
        icon: "folder",
        items: [
          {{ title: "{item_title}", type: "{ftype}", path: "{rel_path}" }}
        ]
      }},
'''
                    insert_pos = sec_bracket + len("sections: [\n")
                    data_text = data_text[:insert_pos] + new_section + data_text[insert_pos:]
                    added_count += 1

        if added_count > 0:
            with open(DATA_JS_PATH, "w", encoding="utf-8") as f:
                f.write(data_text)
            print(f"   📝 تم تسجيل {added_count} ملفاً جديداً في data.js تلقائياً.")
    except Exception as e:
        print(f"   ⚠️ تعذر تحديث data.js تلقائياً: {e}")


def run_git_sync(new_files):
    """إجراء commit و push إلى مستودع الاستضافة"""
    if not new_files:
        return

    update_database_with_new_files(new_files)
    print("\n🚀 جاري تجهيز التحديث ورفعه إلى GitHub...")
    try:
        subprocess.run(["git", "add", "."], cwd=BASE_DIR, check=True)
        course_names = list(set([f["folder"] for f in new_files]))
        files_str = ", ".join([f["filename"] for f in new_files[:3]])
        if len(new_files) > 3:
            files_str += f" (+{len(new_files)-3} files)"
            
        commit_msg = f"feat(moodle-sync): add new materials for {', '.join(course_names)} ({files_str})"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=BASE_DIR, check=True)
        print("   ✅ تم إنشاء الـ Commit بنجاح.")

        print("   🌐 جاري الرفع إلى المستودع (git push origin main)...")
        push_res = subprocess.run(["git", "push", "origin", "main"], cwd=BASE_DIR, capture_output=True, text=True)
        if push_res.returncode == 0:
            print("   🎉 تم رفع التحديثات إلى الاستضافة بنجاح وبشكل فوري!")
        else:
            print(f"   ⚠️ تعذر الرفع: {push_res.stderr}")
    except Exception as e:
        print(f"   ❌ حدث خطأ أثناء تشغيل Git: {e}")


def main():
    parser = argparse.ArgumentParser(description="أداة المزامنة التلقائية مع مودل الجامعة الإسلامية (IUG)")
    parser.add_argument("--no-push", action="store_true", help="تنزيل الملفات وتحديث الموقع محلياً فقط دون الرفع لـ GitHub")
    parser.add_argument("--check-only", action="store_true", help="فحص المواد فقط دون تنزيل")
    args = parser.parse_args()

    print("=" * 65)
    print("🎓 أداة المزامنة الذكية مع مودل الجامعة الإسلامية (IUG Moodle Sync)")
    print("=" * 65)

    env = load_env()
    username = env.get("MOODLE_USERNAME", "").strip()
    password = env.get("MOODLE_PASSWORD", "").strip()
    auto_push = env.get("AUTO_GIT_PUSH", "true").lower() == "true" and not args.no_push

    if not username or not password:
        print("\n⚠️ تنبيه: بيانات الدخول غير موجودة في ملف .env!")
        print("يرجى فتح ملف .env وكتابة رقمك الجامعي وكلمة المرور بالشكل التالي:")
        print("--------------------------------------------------")
        print("MOODLE_USERNAME=رقمك_الجامعي")
        print("MOODLE_PASSWORD=كلمة_مرورك")
        print("--------------------------------------------------")
        return

    # تسجيل الدخول
    syncer = IUGMoodleSync(username, password)
    if not syncer.login():
        return

    # جلب المساقات
    courses = syncer.get_enrolled_courses()
    matched_courses = [c for c in courses if c["mapping"]]

    if not matched_courses:
        print("ℹ️ لم يتم العثور على مقررات مطابقة لمقررات البوابة (نظم تشغيل، اتصالات، أسمبلي).")
        return

    if args.check_only:
        print("\n✅ تم فحص المواد بنجاح (وضع الفحص فقط).")
        return

    # مزامنة المواد
    all_new_files = []
    for c in matched_courses:
        new_files = syncer.sync_course(c)
        all_new_files.extend(new_files)

    # التقرير والرفع
    print("\n" + "=" * 65)
    if all_new_files:
        print(f"🎉 تم تنزيل {len(all_new_files)} ملفاً جديداً بنجاح:")
        for nf in all_new_files:
            print(f"   • [{nf['folder']}] {nf['filename']} ({nf['size_mb']} MB)")

        if auto_push:
            run_git_sync(all_new_files)
        else:
            print("\n💡 تم حفظ الملفات محلياً (تم تعطيل الرفع التلقائي).")
    else:
        print("✨ لا توجد ملفات أو سلايدات جديدة غير محملة على المودل. موقعك محدث بالكامل!")
    print("=" * 65)


if __name__ == "__main__":
    main()
