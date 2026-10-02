#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
أداة المزامنة التلقائية مع مودل الجامعة الإسلامية بغزة (IUG Moodle Sync)
المقررات: نظم تشغيل • اتصالات بيانات • تنظيم حاسوب ولغة أسمبلي
=============================================================================
الوظيفة:
1. تسجيل الدخول الآمن إلى مودل الجامعة عبر بوابة المصادقة الموحدة (SSO)
2. فحص المواد الدراسية وتتبع الملفات وروابط المحاضرات والفيديوهات والتسجيلات الجديدة
3. تنزيل الملفات الجديدة وتنظيف أسمائها تلقائياً
4. تحديث ملفات الروابط (links.txt) وقاعدة البيانات (data.js) وصفحات المقررات (course-*.html)
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
    print("[ERROR] 'requests' library not installed. Install via: pip install requests")
    sys.exit(1)

# إعداد المسارات الأساسية
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
DATA_JS_PATH = BASE_DIR / "data.js"

# خريطة المقررات المعتمدة في البوابة (المقررات النظرية والمعامل التطبيقية)
KNOWN_COURSES = [
    # --- المقررات النظرية (Theory) ---
    {
        "id": "os",
        "db_id": "os",
        "moodle_id": 12297,
        "is_lab": False,
        "keywords": ["نظم تشغيل", "operating systems", "ecom4401"],
        "folder": "OS",
        "page": "course-os.html",
        "title": "نظم تشغيل",
        "video_fn": "playVideo",
        "links_file": "links.txt"
    },
    {
        "id": "data_comm",
        "db_id": "data_comm",
        "moodle_id": 4455,
        "is_lab": False,
        "keywords": ["اتصالات بيانات", "data communication", "data communications", "ecom4411"],
        "folder": "DataCom",
        "page": "course-datacom.html",
        "title": "اتصالات بيانات",
        "video_fn": "playVideo",
        "links_file": "links.txt"
    },
    {
        "id": "assembly",
        "db_id": "assembly",
        "moodle_id": 2463,
        "is_lab": False,
        "keywords": ["تنظيم حاسوب", "أسمبلي", "تجميع", "assembly", "ecom4403", "ecom4412"],
        "folder": "Assembly",
        "page": "course-assembly.html",
        "title": "تنظيم حاسوب ولغة أسمبلي",
        "video_fn": "playYouTube",
        "links_file": "link.txt"
    },
    # --- المعامل والتطبيقات العملية (Laboratories) ---
    {
        "id": "data_comm_lab",
        "db_id": "data_comm_lab",
        "moodle_id": 12191,
        "is_lab": True,
        "parent_id": "data_comm",
        "keywords": ["اتصالات بيانات", "data communication", "data communications", "ecom4002"],
        "folder": "DataCom",
        "page": "course-datacom-lab.html",
        "title": "اتصالات بيانات (عملي)",
        "video_fn": "playVideo",
        "links_file": "links.txt"
    },
    {
        "id": "os_lab",
        "db_id": "os_lab",
        "moodle_id": 12168,
        "is_lab": True,
        "parent_id": "os",
        "keywords": ["نظم تشغيل", "operating systems", "ecom4001"],
        "folder": "OS",
        "page": "course-os-lab.html",
        "title": "نظم تشغيل (عملي)",
        "video_fn": "playVideo",
        "links_file": "links.txt"
    },
    {
        "id": "assembly_lab",
        "db_id": "assembly_lab",
        "moodle_id": 12220,
        "is_lab": True,
        "parent_id": "assembly",
        "keywords": ["تنظيم حاسوب", "أسمبلي", "تجميع", "assembly", "ecom4003"],
        "folder": "Assembly",
        "page": "course-assembly-lab.html",
        "title": "لغة تجميع (عملي)",
        "video_fn": "playYouTube",
        "links_file": "link.txt"
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


def extract_youtube_id(url):
    """استخراج معرّف فيديو يوتيوب من الرابط إن وجد"""
    m = re.search(r'(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|embed\/|v\/|.+\?v=))([a-zA-Z0-9_-]{11})', url)
    return m.group(1) if m else None


def extract_section_info(title, section_name="", is_lab=False):
    """استخراج رقم واسم القسم المنطقي من عنوان العنصر أو اسم القسم (سواء فصل أو معمل)"""
    combined = f"{section_name} {title}"
    
    # 1. التحقق إن كان نشاط معمل / تجربة عملية
    lab_m = re.search(r'(?:lab|معمل|تجربة)[-_\s]*(\d+)', combined, re.IGNORECASE)
    if lab_m or is_lab:
        if lab_m:
            num = int(lab_m.group(1))
            return f"Lab {num}: تجارب المعمل", num
        return "المعمل والتطبيقات العملية (Labs)", None

    # 2. التحقق إن كان فصلاً دراسياً نظرياً (Chapter)
    ch_m = re.search(r'(?:ch(?:apter)?[-_\s]*|0)(\d+)', combined, re.IGNORECASE)
    if ch_m:
        try:
            ch_num = int(ch_m.group(1))
            return f"Chapter {ch_num}", ch_num
        except ValueError:
            pass

    return None, None


def extract_chapter_info(title, section_name=""):
    """استخراج معلومات الفصل للتوافق الرجعي"""
    name, num = extract_section_info(title, section_name, is_lab=False)
    return num, name


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
        print("[SSO] Connecting to authentication portal (sso.iugaza.edu.ps)...")
        try:
            r_sso = self.session.get(self.SAML_URL, allow_redirects=True, timeout=25)
            auth_match = re.search(r'AuthState=([^&]+)', r_sso.url)
            if not auth_match:
                print("[ERROR] Could not extract AuthState session token from SSO.")
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
                print(f"[ERROR] University server returned error: {msg}")
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
            print(f"[ERROR] Exception during login: {e}")
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
                print(f"[OK] Welcome, {self.user_fullname}! (Logged in successfully)")
            else:
                print("[OK] Logged in successfully to student portal!")
            return True
        return False

    def get_enrolled_courses(self):
        """جلب المقررات المسجلة للطالب عبر WebService API المدمج في المودل"""
        print("[COURSES] Fetching enrolled courses from student account...")
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
                        is_lab = ("عملي" in combined) or ("lab" in combined) or any(c in combined for c in ["4001", "4002", "4003"])
                        for mapping in KNOWN_COURSES:
                            if mapping["moodle_id"] == cid:
                                matched_info = mapping
                                break
                            m_is_lab = mapping.get("is_lab", False)
                            if (is_lab == m_is_lab) and any(kw in combined for kw in mapping["keywords"]):
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
                print(f"[WARN] Error calling courses API: {e}")

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

        print(f"[INFO] Found {len(courses)} enrolled course(s):")
        for c in courses:
            if c['mapping']:
                course_type = "معمل عملي" if c['mapping'].get('is_lab') else "نظري"
                status_text = f"-> [Linked to: {c['mapping']['folder']}/ ({c['mapping']['page']}) - {course_type}]"
            else:
                status_text = "(Not in portal)"
            display_title = c.get("shortname") or c.get("title") or f"Course {c['id']}"
            print(f"   * [{c['id']}] {display_title} {status_text}")

        return courses

    def _handle_whatsapp_link(self, url, mapping, title):
        """التحقق من روابط مجموعات الواتساب وتحديث ملف linkslabs.txt إن لزم"""
        try:
            links_lab_path = BASE_DIR / "linkslabs.txt"
            if mapping.get("is_lab"):
                existing = links_lab_path.read_text(encoding="utf-8") if links_lab_path.exists() else ""
                if url not in existing:
                    entry = f"{mapping['title']}/{url}\n"
                    with open(links_lab_path, "a", encoding="utf-8") as f:
                        f.write(entry)
                    print(f"   [WHATSAPP] Added {mapping['title']} WhatsApp link to linkslabs.txt")
                else:
                    print(f"   [WHATSAPP] Verified WhatsApp group for {mapping['title']}.")
        except Exception as e:
            print(f"   [WARN] Error registering WhatsApp link: {e}")

    def sync_course(self, course_info):
        """فحص وتنزيل محتويات المقرر المربوط (ملفات وروابط محاضرات وفيديوهات)"""
        mapping = course_info["mapping"]
        if not mapping:
            return {"files": [], "links": []}

        folder_name = mapping["folder"]
        folder_path = BASE_DIR / folder_name
        folder_path.mkdir(exist_ok=True)
        page_path = BASE_DIR / mapping["page"]
        existing_page_text = page_path.read_text(encoding="utf-8") if page_path.exists() else ""

        links_file_name = mapping.get("links_file", "links.txt")
        links_file_path = folder_path / links_file_name
        existing_links_text = links_file_path.read_text(encoding="utf-8") if links_file_path.exists() else ""

        is_lab = mapping.get("is_lab", False)
        type_badge = "LAB" if is_lab else "THEORY"
        print(f"\n[SCAN] Checking course: {mapping['id'].upper()} ({mapping['folder']}/) [{type_badge}]...")
        r = self.session.get(course_info["url"], timeout=25)
        page_html = r.text

        # 1. استخراج الأقسام والأنشطة وفق بنية Moodle 4
        sec_matches = list(re.finditer(r'<li[^>]+data-for="section"[^>]*data-sectionname="([^"]*)"[^>]*>', page_html))
        activities = []

        if sec_matches:
            for i, sm in enumerate(sec_matches):
                sec_name = sm.group(1).strip()
                sec_start = sm.start()
                sec_end = sec_matches[i+1].start() if i+1 < len(sec_matches) else len(page_html)
                sec_body = page_html[sec_start:sec_end]
                
                acts = re.findall(r'<li[^>]+class="activity\s+([^\s"]+)[^>]*data-id="(\d+)"[^>]*>[\s\S]*?data-activityname="([^"]*)"', sec_body)
                for act_type, act_id, act_name in acts:
                    activities.append({
                        "section_name": sec_name,
                        "type": act_type.lower(),
                        "id": act_id,
                        "name": act_name.strip()
                    })
        else:
            # Fallback للأنشطة بالطريقة الكلاسيكية
            res_ids = set(re.findall(r'/mod/resource/view\.php\?id=(\d+)', page_html))
            url_ids = set(re.findall(r'/mod/url/view\.php\?id=(\d+)', page_html))
            for rid in res_ids:
                activities.append({"section_name": "", "type": "resource", "id": rid, "name": f"Resource {rid}"})
            for uid in url_ids:
                activities.append({"section_name": "", "type": "url", "id": uid, "name": f"URL {uid}"})

        downloaded_new_files = []
        new_links_found = []

        # 2. فحص الأنشطة وتنزيل الملفات
        for act in activities:
            act_type = act["type"]
            act_id = act["id"]
            act_name = act["name"]
            sec_name = act["section_name"]

            # أ) ملفات الموارد (resource)
            if act_type == "resource":
                res_url = f"{self.BASE_URL}/mod/resource/view.php?id={act_id}"
                file_info = self._download_file_if_new(res_url, folder_path, act_name, existing_page_text)
                if file_info:
                    file_info["section_name"] = sec_name
                    file_info["is_lab"] = is_lab
                    file_info["mapping"] = mapping
                    downloaded_new_files.append(file_info)

            # ب) روابط المحاضرات والفيديوهات (url)
            elif act_type == "url":
                # تحقق مبدئي إن كان الرابط أو المحاضرة موجودة مسبقاً في الصفحة أو في links.txt
                # إذا كانت موجودة بالاسم المباشر، نتجاوز طلب الشبكة لسرعة فائقة
                if act_name in existing_page_text and act_name in existing_links_text:
                    continue

                target_url = self._resolve_url_activity(act_id)
                if not target_url:
                    continue
                target_url = target_url.replace("&amp;", "&")

                # إذا كان الرابط هو رابط مجتمع / مجموعة واتساب
                if "chat.whatsapp.com" in target_url:
                    self._handle_whatsapp_link(target_url, mapping, act_name)
                    continue

                yt_id = extract_youtube_id(target_url)
                
                # التحقق إن كان مسجلاً مسبقاً في صفحة المساق
                is_in_page = (target_url in existing_page_text) or (yt_id and yt_id in existing_page_text) or (act_name in existing_page_text)
                
                if not is_in_page:
                    print(f"   [NEW LINK] Found lecture/video: {act_name} -> {target_url}")
                    new_links_found.append({
                        "id": act_id,
                        "title": act_name,
                        "url": target_url,
                        "youtube_id": yt_id,
                        "folder": folder_name,
                        "section_name": sec_name,
                        "is_lab": is_lab,
                        "mapping": mapping,
                        "video_fn": mapping.get("video_fn", "playVideo")
                    })

        return {
            "files": downloaded_new_files,
            "links": new_links_found,
            "mapping": mapping
        }

    def _resolve_url_activity(self, uid):
        """استخراج الرابط الخارجي الفعلي للنشاط (YouTube, Drive, etc.)"""
        try:
            resp = self.session.get(f"{self.BASE_URL}/mod/url/view.php?id={uid}", timeout=15)
            # 1. البحث في كلاس urlworkaround القياسي في مودل
            m_workaround = re.search(r'class=["\']urlworkaround["\'][^>]*><a[^>]+href=["\']([^"\']+)["\']', resp.text)
            if m_workaround:
                url = m_workaround.group(1).strip()
                if "moodle.com" not in url:
                    return url

            # 2. البحث عن أي رابط خارجي في الصفحة
            links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', resp.text)
            for href, _ in links:
                if "logout" not in href and "theme" not in href and ("http" in href):
                    if "moodle.iugaza.edu.ps" not in href and "moodle.com" not in href:
                        return href.strip()
            return None
        except Exception:
            return None

    def _download_file_if_new(self, url, target_dir, fallback_title="", page_text=""):
        """تنزيل الملف في حال كان جديداً وغير مكرر، ومعالجة الموارد المضمنة"""
        try:
            head = self.session.head(url, allow_redirects=True, timeout=15)
            content_type = head.headers.get("Content-Type", "")
            content_disp = head.headers.get("Content-Disposition", "")
            download_url = head.url

            # إذا كانت الاستجابة HTML (مثل ملفات PDF/الفيديوهات المضمنة داخل صفحة المودل)
            if "text/html" in content_type:
                get_page = self.session.get(url, timeout=15)
                # البحث عن رابط pluginfile.php المضمن
                p_match = re.search(r'https?://moodle\.iugaza\.edu\.ps/pluginfile\.php/[^\s"\'<>]+', get_page.text)
                if p_match:
                    download_url = p_match.group(0)
                    head = self.session.head(download_url, allow_redirects=True, timeout=15)
                    content_disp = head.headers.get("Content-Disposition", "")
                else:
                    return None

            filename = None
            if "filename=" in content_disp:
                fn_match = re.search(r'filename\*?=(?:UTF-8\'\')?["\']?([^"\';]+)["\']?', content_disp)
                if fn_match:
                    filename = urllib.parse.unquote(fn_match.group(1))

            if not filename:
                filename = os.path.basename(urllib.parse.urlparse(download_url).path)

            if not filename or filename == "view.php":
                if fallback_title:
                    filename = fallback_title
                else:
                    return None

            clean_filename = self._clean_filename(filename)
            target_file = target_dir / clean_filename

            # التحقق إن كان الملف موجوداً مسبقاً بنفس الحجم
            content_length = int(head.headers.get("Content-Length", 0))
            file_already_on_disk = target_file.exists() and content_length > 0 and (target_file.stat().st_size == content_length)

            rel_path = f"{target_dir.name}/{clean_filename}"
            is_in_page = rel_path in page_text

            # إذا كان الملف موجوداً على القرص ومسجلاً بالصفحة فلا داعي لإعادة تنزيله
            if file_already_on_disk and is_in_page:
                return None

            # إذا لم يكن موجوداً على القرص ننزله
            if not file_already_on_disk:
                print(f"   [DOWNLOAD] Fetching new file: {clean_filename} ...")
                resp = self.session.get(download_url, stream=True, timeout=45)
                with open(target_file, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)

            size_mb = round(target_file.stat().st_size / (1024 * 1024), 2)
            if not file_already_on_disk:
                print(f"   [SAVED] {clean_filename} ({size_mb} MB)")

            return {
                "filename": clean_filename,
                "relative_path": rel_path,
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


def update_links_files(new_links):
    """إضافة أي روابط جديدة تم اكتشافها إلى ملفات links.txt الخاصة بكل مقرر"""
    if not new_links:
        return

    for item in new_links:
        folder = item["folder"]
        mapping = next((m for m in KNOWN_COURSES if m["folder"] == folder), None)
        links_name = mapping.get("links_file", "links.txt") if mapping else "links.txt"
        links_path = BASE_DIR / folder / links_name

        try:
            current_text = links_path.read_text(encoding="utf-8") if links_path.exists() else ""
            line_to_add = f"{item['title']} / {item['url']}"
            if item['title'] not in current_text and item['url'] not in current_text:
                updated_text = current_text.strip() + "\n" + line_to_add + "\n"
                links_path.write_text(updated_text, encoding="utf-8")
                print(f"   [LINKS] Added {item['title']} to {folder}/{links_name}")
        except Exception as e:
            print(f"   [WARN] Could not update {links_name}: {e}")


def update_course_pages_with_items(new_files, new_links):
    """إضافة الملفات والفيديوهات الجديدة تلقائياً إلى صفحات المقررات بتصميم HP الأكاديمي الموحد"""
    all_items = []
    for f in new_files:
        all_items.append({"kind": "file", **f})
    for l in new_links:
        all_items.append({"kind": "link", **l})

    if not all_items:
        return

    items_by_course = {}
    for it in all_items:
        mapping = it.get("mapping")
        cid = mapping.get("id") if mapping else it.get("folder")
        items_by_course.setdefault(cid, {"mapping": mapping, "items": []})["items"].append(it)

    for cid, cdata in items_by_course.items():
        mapping = cdata["mapping"]
        if not mapping:
            continue

        page_name = mapping.get("page")
        if not page_name:
            continue

        items = cdata["items"]
        html_path = BASE_DIR / page_name
        if not html_path.exists():
            continue

        try:
            with open(html_path, "r", encoding="utf-8") as f:
                html_text = f.read()

            modified = False
            for it in items:
                kind = it["kind"]

                if kind == "file":
                    rel_path = it["relative_path"]
                    if rel_path in html_text:
                        continue

                    filename = it["filename"]
                    ext = Path(filename).suffix.lower().replace(".", "")
                    item_title = Path(filename).stem
                    size_mb = it.get("size_mb", 0)

                    if ext in ["ppt", "pptx"]:
                        icon_color = "color: #d97706;"
                        icon_name = "presentation"
                        file_subinfo = f"عرض تقديمي PowerPoint • {size_mb} MB • سلايدات المحاضرة"
                        preview_btn = ""
                    elif ext == "pdf":
                        icon_color = "color: var(--color-bloom-coral);"
                        icon_name = "file-text"
                        file_subinfo = f"ملف PDF • {size_mb} MB • المادة العلمية المعتمدة"
                        preview_btn = f'''                <a href="{rel_path}" target="_blank" class="btn btn-outline-ink btn-sm">
                  <i data-lucide="eye" class="lucide-sm"></i>
                  <span>معاينة</span>
                </a>\n'''
                    elif ext in ["mp4", "webm"]:
                        icon_color = "color: #ff0000;"
                        icon_name = "play-circle"
                        file_subinfo = f"تسجيل فيديو • {size_mb} MB"
                        preview_btn = f'''                <button class="btn btn-primary btn-sm" onclick="playLocalVideo('{rel_path}', '{item_title}')">
                  <i data-lucide="play" class="lucide-sm"></i>
                  <span>تشغيل الفيديو</span>
                </button>\n'''
                    else:
                        icon_color = "color: var(--color-primary);"
                        icon_name = "file"
                        file_subinfo = f"ملف مرفق • {size_mb} MB"
                        preview_btn = ""

                    row_html = f'''            <!-- {filename} -->
            <div class="moodle-file-row">
              <div class="file-row-left">
                <div class="file-type-square" style="{icon_color}">
                  <i data-lucide="{icon_name}"></i>
                </div>
                <div class="file-meta-text">
                  <div class="file-name-heading">{item_title}</div>
                  <span class="file-subinfo">{file_subinfo}</span>
                </div>
              </div>
              <div class="file-row-actions">
{preview_btn}                <a href="{rel_path}" download class="btn btn-primary btn-sm">
                  <i data-lucide="download" class="lucide-sm"></i>
                  <span>تحميل</span>
                </a>
                <button class="btn btn-outline-ink btn-sm btn-copy" onclick="copyFilePath('{rel_path}')" title="نسخ المسار">
                  <i data-lucide="copy" class="lucide-sm"></i>
                </button>
              </div>
            </div>'''
                    ch_num, _ = extract_chapter_info(filename, it.get("section_name", ""))

                else:
                    # Link / Video
                    url = it["url"]
                    yt_id = it.get("youtube_id")
                    if url in html_text or (yt_id and yt_id in html_text):
                        continue

                    title = it["title"]
                    video_fn = it.get("video_fn", "playVideo")

                    if yt_id:
                        row_html = f'''            <!-- {title} -->
            <div class="moodle-file-row">
              <div class="file-row-left">
                <div class="file-type-square" style="color: #ff0000;">
                  <i data-lucide="play-circle"></i>
                </div>
                <div class="file-meta-text">
                  <div class="file-name-heading">{title}</div>
                  <span class="file-subinfo">تسجيل فيديو YouTube • محاضرة وشرح المادة</span>
                </div>
              </div>
              <div class="file-row-actions">
                <button class="btn btn-primary btn-sm" onclick="{video_fn}('{yt_id}', '{title}')">
                  <i data-lucide="play" class="lucide-sm"></i>
                  <span>تشغيل المحاضرة</span>
                </button>
                <a href="{url}" target="_blank" rel="noopener noreferrer" class="btn btn-outline-ink btn-sm">
                  <i data-lucide="external-link" class="lucide-sm"></i>
                  <span>YouTube</span>
                </a>
              </div>
            </div>'''
                    else:
                        row_html = f'''            <!-- {title} -->
            <div class="moodle-file-row">
              <div class="file-row-left">
                <div class="file-type-square" style="color: var(--color-primary);">
                  <i data-lucide="external-link"></i>
                </div>
                <div class="file-meta-text">
                  <div class="file-name-heading">{title}</div>
                  <span class="file-subinfo">رابط خارجي • المادة الأكاديمية</span>
                </div>
              </div>
              <div class="file-row-actions">
                <a href="{url}" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-sm">
                  <i data-lucide="external-link" class="lucide-sm"></i>
                  <span>فتح الرابط</span>
                </a>
                <button class="btn btn-outline-ink btn-sm btn-copy" onclick="copyFilePath('{url}')" title="نسخ الرابط">
                  <i data-lucide="copy" class="lucide-sm"></i>
                </button>
              </div>
            </div>'''
                is_lab_item = it.get("is_lab", False) or (mapping and mapping.get("is_lab", False))
                sec_label, ch_num = extract_section_info(it.get("filename") or it.get("title"), it.get("section_name", ""), is_lab=is_lab_item)

                # إدراج العنصر داخل قسم الفصل أو المعمل المناسب في الصفحة
                section_found = False
                if is_lab_item:
                    lab_pattern = re.compile(
                        r'(<section[^>]*class=["\'][^"\']*moodle-section-card[^"\']*["\'][^>]*id=["\']lab-section["\'][^>]*>[\s\S]*?<div[^>]*class=["\'][^"\']*moodle-files-list[^"\']*["\'][^>]*>)([\s\S]*?)(</div>\s*</div>\s*</section>)',
                        re.IGNORECASE
                    )
                    m_lab = lab_pattern.search(html_text)
                    if not m_lab:
                        lab_pattern = re.compile(
                            r'(<section[^>]*class=["\'][^"\']*moodle-section-card[^"\']*["\'][^>]*>[\s\S]*?<div[^>]*class=["\'][^"\']*moodle-section-head[^"\']*["\'][^>]*>[\s\S]*?(?:المعمل|Lab Experiments|تجارب المعمل)[\s\S]*?<div[^>]*class=["\'][^"\']*moodle-files-list[^"\']*["\'][^>]*>)([\s\S]*?)(</div>\s*</div>\s*</section>)',
                            re.IGNORECASE
                        )
                        m_lab = lab_pattern.search(html_text)

                    if m_lab:
                        before = m_lab.group(1)
                        content = m_lab.group(2)
                        after = m_lab.group(3)
                        updated_sec = f"{before}{content}\n{row_html}\n          {after}"
                        html_text = html_text[:m_lab.start()] + updated_sec + html_text[m_lab.end():]
                        section_found = True
                        modified = True
                        print(f"   [HTML] Added {it.get('filename') or it.get('title')} to Lab Section in ({page_name}).")
                    else:
                        lab_title = f"المعمل والتطبيقات العملية ({mapping.get('title', 'Lab')})"
                        new_section_card = f'''
      <!-- ========================================================
           القسم: {lab_title}
           ======================================================== -->
      <section class="moodle-section-card" id="lab-section">
        <div class="moodle-section-head">
          <h3>
            <i data-lucide="flask-conical" class="lucide-sm" style="color: var(--color-primary);"></i>
            <span>{lab_title}</span>
          </h3>
          <span class="stat-pill" style="border-color: var(--color-primary); color: var(--color-primary);">تجارب المعمل</span>
        </div>
        <div class="moodle-section-body">
          <div class="moodle-files-list">
{row_html}
          </div>
        </div>
      </section>
'''
                        close_wrap_match = re.search(r'(\s*</div>\s*</main>)', html_text)
                        if close_wrap_match:
                            pos = close_wrap_match.start(1)
                            html_text = html_text[:pos] + new_section_card + html_text[pos:]
                            section_found = True
                            modified = True
                            print(f"   [HTML] Created Lab Section with {it.get('filename') or it.get('title')} in ({page_name}).")

                elif ch_num is not None:
                    sec_pattern = re.compile(
                        rf'(<section[^>]*class=["\'][^"\']*moodle-section-card[^"\']*["\'][^>]*>[\s\S]*?Chapter\s*{ch_num}[:\s\(\)][\s\S]*?<div[^>]*class=["\'][^"\']*moodle-files-list[^"\']*["\'][^>]*>)([\s\S]*?)(</div>\s*</div>\s*</section>)',
                        re.IGNORECASE
                    )
                    match = sec_pattern.search(html_text)
                    if match:
                        before = match.group(1)
                        content = match.group(2)
                        after = match.group(3)
                        updated_sec = f"{before}{content}\n{row_html}\n          {after}"
                        html_text = html_text[:match.start()] + updated_sec + html_text[match.end():]
                        section_found = True
                        modified = True
                        print(f"   [HTML] Added {it.get('filename') or it.get('title')} to Chapter {ch_num} in ({page_name}).")

                # إذا لم يكن قسم الشابتر موجوداً، ننشئ قسماً جديداً له
                if not section_found:
                    heading_title = sec_label or (it.get('title') or it.get('filename'))
                    new_section_card = f'''
      <!-- ========================================================
           القسم: {heading_title}
           ======================================================== -->
      <section class="moodle-section-card">
        <div class="moodle-section-head">
          <h3>
            <i data-lucide="folder" class="lucide-sm" style="color: var(--color-primary);"></i>
            <span>{heading_title}</span>
          </h3>
        </div>
        <div class="moodle-section-body">
          <div class="moodle-files-list">
{row_html}
          </div>
        </div>
      </section>
'''
                    close_wrap_match = re.search(r'(\s*</div>\s*</main>)', html_text)
                    if close_wrap_match:
                        pos = close_wrap_match.start(1)
                        html_text = html_text[:pos] + new_section_card + html_text[pos:]
                        modified = True
                        print(f"   [HTML] Created new section for {it.get('title') or it.get('filename')} in ({page_name}).")

            if modified:
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_text)
                print(f"   [OK] Course page ({page_name}) updated successfully.")
        except Exception as e:
            print(f"   [WARN] Could not update page ({page_name}) automatically: {e}")


def update_database_with_items(new_files, new_links):
    """إضافة أي ملفات أو فيديوهات جديدة إلى قاعدة بيانات data.js بشكل منظم ومرتب"""
    all_items = []
    for f in new_files:
        all_items.append({"kind": "file", **f})
    for l in new_links:
        all_items.append({"kind": "link", **l})

    if not all_items or not DATA_JS_PATH.exists():
        return

    try:
        with open(DATA_JS_PATH, "r", encoding="utf-8") as f:
            data_text = f.read()

        added_count = 0
        for it in all_items:
            kind = it["kind"]
            mapping = it.get("mapping")
            folder = it["folder"]
            is_lab = it.get("is_lab", False) or (mapping and mapping.get("is_lab", False))

            # تحديد معرّف المساق في قاعدة البيانات (data.js)
            if mapping and mapping.get("db_id"):
                course_id = mapping["db_id"]
            elif is_lab:
                course_id = f"{folder.lower()}_lab"
            else:
                course_id = "os" if folder == "OS" else ("data_comm" if folder == "DataCom" else "assembly")

            if kind == "file":
                rel_path = it["relative_path"]
                if rel_path in data_text:
                    continue
                filename = it["filename"]
                ext = Path(filename).suffix.lower().replace(".", "")
                ftype = "ppt" if ext in ["ppt", "pptx"] else ("pdf" if ext == "pdf" else ("video" if ext in ["mp4", "webm"] else "doc"))
                stem = Path(filename).stem
                item_title = stem.replace("__", " - ").replace("_", " ").strip()
                item_path = rel_path
                sec_label, ch_num = extract_section_info(filename, it.get("section_name", ""), is_lab=is_lab)
            else:
                url = it["url"]
                yt_id = it.get("youtube_id")
                if url in data_text or (yt_id and yt_id in data_text):
                    continue
                item_title = it["title"]
                item_path = url
                ftype = "video" if yt_id else "link"
                sec_label, ch_num = extract_section_info(item_title, it.get("section_name", ""), is_lab=is_lab)

            course_marker = f'id: "{course_id}"'
            c_idx = data_text.find(course_marker)
            if c_idx == -1:
                continue

            sec_idx = data_text.find("sections: [", c_idx)
            if sec_idx == -1:
                continue

            # العثور على قوس إغلاق sections الخاص بهذا المقرر
            open_count = 0
            close_idx = -1
            for i in range(sec_idx + len("sections: [") - 1, len(data_text)):
                if data_text[i] == '[':
                    open_count += 1
                elif data_text[i] == ']':
                    open_count -= 1
                    if open_count == 0:
                        close_idx = i
                        break

            if close_idx == -1:
                continue

            course_sections_str = data_text[sec_idx:close_idx]

            found_existing_section = False
            sec_icon = "flask-conical" if is_lab else "folder"
            target_sec_title = sec_label or ("تجارب المعمل (Labs)" if is_lab else (f"Chapter {ch_num}" if ch_num is not None else item_title))

            if not is_lab and ch_num is not None:
                ch_pattern = re.compile(rf'(title:\s*["\'][^"\']*Chapter\s*{ch_num}[:\s\(\)][^"\']*["\'][\s\S]*?items:\s*\[)([\s\S]*?)(\])', re.IGNORECASE)
                m_ch = ch_pattern.search(course_sections_str)
                if m_ch:
                    abs_insert_pos = sec_idx + m_ch.end(1)
                    new_item_str = f'\n          {{ title: "{item_title}", type: "{ftype}", path: "{item_path}" }},'
                    data_text = data_text[:abs_insert_pos] + new_item_str + data_text[abs_insert_pos:]
                    found_existing_section = True
                    added_count += 1
            elif is_lab:
                lab_pattern = re.compile(r'(title:\s*["\'][^"\']*(?:Labs|المعمل|تجارب)[^"\']*["\'][\s\S]*?items:\s*\[)([\s\S]*?)(\])', re.IGNORECASE)
                m_lab = lab_pattern.search(course_sections_str)
                if m_lab:
                    abs_insert_pos = sec_idx + m_lab.end(1)
                    new_item_str = f'\n          {{ title: "{item_title}", type: "{ftype}", path: "{item_path}" }},'
                    data_text = data_text[:abs_insert_pos] + new_item_str + data_text[abs_insert_pos:]
                    found_existing_section = True
                    added_count += 1

            if not found_existing_section:
                sec_title = target_sec_title
                new_section = f'''      {{
        title: "{sec_title}",
        icon: "{sec_icon}",
        items: [
          {{ title: "{item_title}", type: "{ftype}", path: "{item_path}" }}
        ]
      }},
'''
                inner_content = course_sections_str[len("sections: ["):].strip()
                if not inner_content:
                    data_text = data_text[:sec_idx + len("sections: [")] + "\n" + new_section + "    " + data_text[close_idx:]
                else:
                    data_text = data_text[:close_idx] + new_section + "    " + data_text[close_idx:]
                added_count += 1

        if added_count > 0:
            with open(DATA_JS_PATH, "w", encoding="utf-8") as f:
                f.write(data_text)
            print(f"   [DATA.JS] Registered {added_count} new item(s) in data.js successfully.")
    except Exception as e:
        print(f"   [WARN] Could not update data.js automatically: {e}")


def run_git_sync(new_files=None, new_links=None):
    """إجراء commit و push إلى مستودع الاستضافة بشكل تلقائي وموثوق"""
    new_files = new_files or []
    new_links = new_links or []
    total_count = len(new_files) + len(new_links)

    print("\n[GIT] Synchronizing and pushing updates to remote repository (GitHub Pages)...")
    try:
        # 1. إضافة كافة الملفات والتعديلات
        subprocess.run(["git", "add", "."], cwd=BASE_DIR, check=True)

        # 2. فحص إن كان هناك تغييرات غير محفوظة (Uncommitted changes)
        status_res = subprocess.run(["git", "status", "--porcelain"], cwd=BASE_DIR, capture_output=True, text=True, check=True)
        has_changes = bool(status_res.stdout.strip())

        if has_changes:
            if total_count > 0:
                courses = list(set([it.get("mapping", {}).get("title") or it["folder"] for it in new_files + new_links]))
                sample_names = [it.get("filename") or it.get("title") for it in (new_files + new_links)[:3]]
                sample_str = ", ".join(sample_names)
                if total_count > 3:
                    sample_str += f" (+{total_count-3} items)"
                commit_msg = f"feat(moodle-sync): sync {total_count} new materials for {', '.join(courses)} ({sample_str})"
            else:
                commit_msg = "chore(sync): update course materials, lab pages, and links"

            commit_res = subprocess.run(["git", "commit", "-m", commit_msg], cwd=BASE_DIR, capture_output=True, text=True)
            if commit_res.returncode == 0:
                print("   [OK] Git commit created successfully.")
            else:
                print(f"   [INFO] Git commit status: {commit_res.stdout.strip() or commit_res.stderr.strip()}")
        else:
            print("   [INFO] Local working tree is clean (no uncommitted file modifications).")

        # 3. دفع التحديثات إلى المستودع البعيد (git push origin main)
        print("   [GIT] Pushing commits to remote repository (git push origin main)...")
        push_res = subprocess.run(["git", "push", "origin", "main"], cwd=BASE_DIR, capture_output=True, text=True)
        if push_res.returncode == 0:
            if "Everything up-to-date" in push_res.stdout or "Everything up-to-date" in push_res.stderr:
                print("   [OK] Remote repository is already fully up to date.")
            else:
                print("   [SUCCESS] All updates and materials pushed to GitHub hosting successfully!")
        else:
            err_msg = push_res.stderr.strip() or push_res.stdout.strip()
            print(f"   [WARN] Git push warning/error: {err_msg}")
    except Exception as e:
        print(f"   [ERROR] Git sync execution error: {e}")


def main():
    parser = argparse.ArgumentParser(description="IUG Moodle Automated Synchronization Tool")
    parser.add_argument("--no-push", action="store_true", help="Download and update locally without pushing to GitHub")
    parser.add_argument("--check-only", action="store_true", help="Check courses only without downloading")
    args = parser.parse_args()

    print("=" * 65)
    print("  IUG Moodle Smart Synchronization Tool")
    print("=" * 65)

    env = load_env()
    username = env.get("MOODLE_USERNAME", "").strip()
    password = env.get("MOODLE_PASSWORD", "").strip()
    auto_push = env.get("AUTO_GIT_PUSH", "true").lower() == "true" and not args.no_push

    if not username or not password:
        print("\n[WARN] Login credentials not found in .env file!")
        print("Please open .env and set your university ID and password:")
        print("--------------------------------------------------")
        print("MOODLE_USERNAME=your_student_id")
        print("MOODLE_PASSWORD=your_password")
        print("--------------------------------------------------")
        return

    # Login
    syncer = IUGMoodleSync(username, password)
    if not syncer.login():
        return

    # Fetch enrolled courses
    courses = syncer.get_enrolled_courses()
    matched_courses = [c for c in courses if c["mapping"]]

    if not matched_courses:
        print("[INFO] No matching courses found for portal (OS, DataCom, Assembly).")
        return

    if args.check_only:
        print("\n[OK] Courses checked successfully (check-only mode).")
        return

    # Sync courses
    all_new_files = []
    all_new_links = []
    for c in matched_courses:
        res = syncer.sync_course(c)
        all_new_files.extend(res.get("files", []))
        all_new_links.extend(res.get("links", []))

    # Report, update, and push
    total_new = len(all_new_files) + len(all_new_links)
    print("\n" + "=" * 65)
    if total_new > 0:
        print(f"[OK] Detected {total_new} new item(s) from Moodle:")
        for nf in all_new_files:
            print(f"   * [FILE - {nf['folder']}] {nf['filename']} ({nf['size_mb']} MB)")
        for nl in all_new_links:
            print(f"   * [LINK - {nl['folder']}] {nl['title']} -> {nl['url']}")

        # Update links text files
        update_links_files(all_new_links)

        # Always update local database and course pages
        update_course_pages_with_items(all_new_files, all_new_links)
        update_database_with_items(all_new_files, all_new_links)
    else:
        print("[OK] All courses are fully up to date. No new materials found on Moodle.")

    # Always synchronize and push to remote if auto_push is enabled
    if auto_push:
        run_git_sync(all_new_files, all_new_links)
    else:
        print("\n[INFO] Auto-push is disabled (AUTO_GIT_PUSH=false or --no-push used).")

    print("=" * 65)


if __name__ == "__main__":
    main()
