#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
أداة المزامنة التلقائية مع مودل الجامعة الإسلامية بغزة (IUG Moodle Sync)
المقررات: نظم تشغيل • اتصالات بيانات • تنظيم حاسوب ولغة أسمبلي
=============================================================================
الوظيفة:
1. تسجيل الدخول الآمن إلى مودل الجامعة (IUG) باستخدام بياناتك في ملف .env
2. فحص المواد الدراسية المسجلة وتحديد أي محاضرات أو سلايدات أو تكليفات جديدة
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

# خريطة المقررات بين مودل والمجلدات المحلية
COURSE_MAPPINGS = [
    {
        "id": "os",
        "keywords": ["نظم تشغيل", "operating systems", "ecom4401"],
        "folder": "OS",
        "page": "course-os.html",
        "title": "نظم تشغيل"
    },
    {
        "id": "data_comm",
        "keywords": ["اتصالات بيانات", "data communication", "data communications", "ecom4411"],
        "folder": "DataCom",
        "page": "course-datacom.html",
        "title": "اتصالات بيانات"
    },
    {
        "id": "assembly",
        "keywords": ["تنظيم حاسوب", "أسمبلي", "تجميع", "assembly", "ecom4403"],
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
    LOGIN_URL = "https://moodle.iugaza.edu.ps/login/index.php"
    SAML_URL = "https://moodle.iugaza.edu.ps/auth/saml2/login.php?wants&idp=907e0c01dccba9d62ae57512cec18ed8&passive=off"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})
        self.is_logged_in = False
        self.user_fullname = ""

    def login(self):
        """تسجيل الدخول إلى مودل (يدعم المباشر ومصادقة SSO)"""
        print("🔄 جاري الاتصال ببوابة المودل (moodle.iugaza.edu.ps)...")
        
        # 1. محاولة تسجيل الدخول المباشر
        try:
            r = self.session.get(self.LOGIN_URL, timeout=20)
            token_match = re.search(r'name=["\']logintoken["\'] value=["\']([^"\']+)["\']', r.text)
            
            if token_match:
                login_token = token_match.group(1)
                login_data = {
                    "username": self.username,
                    "password": self.password,
                    "logintoken": login_token,
                    "anchor": ""
                }
                res = self.session.post(self.LOGIN_URL, data=login_data, allow_redirects=True, timeout=25)
                
                # فحص نجاح تسجيل الدخول
                if "login/index.php" not in res.url or 'sesskey' in res.text:
                    if self._verify_login(res.text):
                        print("✅ تم تسجيل الدخول المباشر بنجاح!")
                        self.is_logged_in = True
                        return True
        except Exception as e:
            print(f"⚠️ تنبيه أثناء تسجيل الدخول المباشر: {e}")

        # 2. في حال تطلب نظام المصادقة الموحد (SSO SimpleSAML)
        print("🔄 جاري المحاولة عبر بوابة المصادقة الموحدة (SSO)...")
        try:
            sso_page = self.session.get(self.SAML_URL, allow_redirects=True, timeout=25)
            auth_match = re.search(r'AuthState=([^&]+)', sso_page.url)
            
            if auth_match:
                auth_state = urllib.parse.unquote(auth_match.group(1))
                sso_post = self.session.post(
                    sso_page.url,
                    data={
                        "username": self.username,
                        "password": self.password,
                        "AuthState": auth_state
                    },
                    allow_redirects=True,
                    timeout=25
                )
                
                # قد يكون هناك إعادة توجيه SAML Response عبر نموذج POST مخفي
                if 'name="SAMLResponse"' in sso_post.text:
                    saml_resp_match = re.search(r'name="SAMLResponse" value="([^"]+)"', sso_post.text)
                    saml_action_match = re.search(r'action="([^"]+)"', sso_post.text)
                    if saml_resp_match and saml_action_match:
                        saml_action = saml_action_match.group(1)
                        saml_resp = saml_resp_match.group(1)
                        final_res = self.session.post(
                            saml_action,
                            data={"SAMLResponse": saml_resp},
                            allow_redirects=True,
                            timeout=25
                        )
                        if self._verify_login(final_res.text):
                            print("✅ تم تسجيل الدخول عبر المصادقة الموحدة (SSO) بنجاح!")
                            self.is_logged_in = True
                            return True
                elif self._verify_login(sso_post.text):
                    print("✅ تم تسجيل الدخول عبر المصادقة الموحدة (SSO) بنجاح!")
                    self.is_logged_in = True
                    return True
        except Exception as e:
            print(f"❌ خطأ أثناء الاتصال بنظام SSO: {e}")

        print("❌ فشل تسجيل الدخول. يرجى التأكد من صحة الرقم الجامعي وكلمة المرور في ملف .env")
        return False

    def _verify_login(self, html_text):
        """التحقق من حالة الجلسة واسم الطالب"""
        if "sesskey" in html_text or "my/" in html_text or "logout.php" in html_text:
            name_match = re.search(r'class="usertext mr-1"[^>]*>([^<]+)<', html_text)
            if not name_match:
                name_match = re.search(r'class="userbutton"[^>]*>.*?<span[^>]*>([^<]+)</span>', html_text, re.DOTALL)
            if name_match:
                self.user_fullname = name_match.group(1).strip()
                print(f"👤 مرحباً بك: {self.user_fullname}")
            return True
        return False

    def get_enrolled_courses(self):
        """جلب قائمة المساقات المسجلة للطالب"""
        print("📚 جاري جلب قائمة المقررات الدراسية من حسابك...")
        courses = []
        r = self.session.get(f"{self.BASE_URL}/my/", timeout=25)
        
        # استخراج روابط المقررات
        found_links = set(re.findall(r'https?://moodle\.iugaza\.edu\.ps/course/view\.php\?id=(\d+)', r.text))
        
        # استخراج عناوين المواد
        for cid in sorted(found_links):
            # البحث عن اسم المساق في الصفحة
            title_pattern = rf'href="[^"]*view\.php\?id={cid}"[^>]*>(?:<span[^>]*>)?([^<]+)(?:</span>)?</a>'
            title_match = re.search(title_pattern, r.text)
            title = title_match.group(1).strip() if title_match else f"Course {cid}"
            
            # مطابقة المساق مع مساقاتنا المعتمدة
            matched_info = None
            for mapping in COURSE_MAPPINGS:
                for kw in mapping["keywords"]:
                    if kw in title.lower():
                        matched_info = mapping
                        break
                if matched_info:
                    break

            courses.append({
                "id": cid,
                "url": f"{self.BASE_URL}/course/view.php?id={cid}",
                "title": title,
                "mapping": matched_info
            })

        print(f"ℹ️ تم العثور على {len(courses)} مقرراً دراسياً.")
        for c in courses:
            matched_str = f"➡️ [مربوط مع: {c['mapping']['title']}]" if c['mapping'] else "(غير مشمول في البوابة)"
            print(f"   • {c['title']} (ID: {c['id']}) {matched_str}")

        return courses

    def sync_course(self, course_info):
        """فحص وتنزيل محتويات المقرر المربوط"""
        mapping = course_info["mapping"]
        if not mapping:
            return []

        folder_name = mapping["folder"]
        folder_path = BASE_DIR / folder_name
        folder_path.mkdir(exist_ok=True)

        print(f"\n🔍 جاري فحص مقرر: {mapping['title']} (مجلد: {folder_name}/)...")
        r = self.session.get(course_info["url"], timeout=25)
        
        # استخراج الروابط القابلة للتنزيل
        # 1. روابط الموارد المباشرة resource
        resource_ids = set(re.findall(r'/mod/resource/view\.php\?id=(\d+)', r.text))
        # 2. روابط الملفات pluginfile
        plugin_files = set(re.findall(r'https?://moodle\.iugaza\.edu\.ps/pluginfile\.php/[^\s"\'<>]+', r.text))

        downloaded_new_files = []

        # فحص وتنزيل الموارد
        for rid in resource_ids:
            res_url = f"{self.BASE_URL}/mod/resource/view.php?id={rid}"
            downloaded = self._download_file_if_new(res_url, folder_path)
            if downloaded:
                downloaded_new_files.append(downloaded)

        for pfile in plugin_files:
            downloaded = self._download_file_if_new(pfile, folder_path)
            if downloaded:
                downloaded_new_files.append(downloaded)

        return downloaded_new_files

    def _download_file_if_new(self, url, target_dir):
        """تنزيل الملف في حال كان جديداً وغير مكرر"""
        try:
            head = self.session.head(url, allow_redirects=True, timeout=15)
            content_type = head.headers.get("Content-Type", "")
            content_disp = head.headers.get("Content-Disposition", "")
            
            # تجاهل صفحات HTML
            if "text/html" in content_type:
                # محاولة فحص الصفحة نفسها إذا كانت تحوي رابط تحميل مباشر
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

            # تنظيف اسم الملف
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
        # إزالة (1) و (2)
        name = re.sub(r'\s*\(\d+\)', '', name)
        # استبدال المسافات الزائدة
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

    # تحديث قاعدة البيانات أولاً
    update_database_with_new_files(new_files)

    print("\n🚀 جاري تجهيز التحديث ورفعه إلى GitHub...")
    try:
        # إضافة الملفات الجديدة
        subprocess.run(["git", "add", "."], cwd=BASE_DIR, check=True)
        
        # إنشاء رسالة الالتزام
        course_names = list(set([f["folder"] for f in new_files]))
        files_str = ", ".join([f["filename"] for f in new_files[:3]])
        if len(new_files) > 3:
            files_str += f" (+{len(new_files)-3} files)"
            
        commit_msg = f"feat(moodle-sync): add new materials for {', '.join(course_names)} ({files_str})"
        
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=BASE_DIR, check=True)
        print("   ✅ تم إنشاء الـ Commit بنجاح.")

        # دفع التغييرات
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

    # 1. التحقق من ملف .env
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
        print("💡 تم إنشاء نموذج جاهز باسم `.env.example` يمكنك نسخه وتسميته `.env`.")
        return

    # 2. تسجيل الدخول
    syncer = IUGMoodleSync(username, password)
    if not syncer.login():
        return

    # 3. جلب المساقات
    courses = syncer.get_enrolled_courses()
    matched_courses = [c for c in courses if c["mapping"]]

    if not matched_courses:
        print("ℹ️ لم يتم العثور على مقررات مطابقة لمقررات البوابة (نظم تشغيل، اتصالات، أسمبلي).")
        return

    if args.check_only:
        print("\n✅ تم فحص المواد بنجاح (وضع الفحص فقط).")
        return

    # 4. مزامنة كل مساق
    all_new_files = []
    for c in matched_courses:
        new_files = syncer.sync_course(c)
        all_new_files.extend(new_files)

    # 5. التقرير والرفع
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
        print("✨ لا توجد ملفات أو سلايدات جديدة على المودل. موقعك محدث بالكامل!")
    print("=" * 65)


if __name__ == "__main__":
    main()
