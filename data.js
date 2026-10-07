// قاعدة بيانات المقررات الدراسية المعتمدة - قسم هندسة الحاسوب والاتصالات
// نظيفة وخالية من أي ملفات وهمية، معتمدة بالكامل على المواد الأصلية وروابط الدفعة الرسمية
var COURSES_DATA = [
  {
    id: "data_comm",
    code: "ECOM4411-6249",
    pageUrl: "course-datacom.html",
    title: "اتصالات بيانات",
    englishTitle: "Data Communications",
    category: "theory",
    semester: "خريف 2026 (Fall 2026)",
    icon: "radio",
    description: "مقرر اتصالات البيانات وشبكات الحاسوب، دراسة نماذج OSI و TCP/IP، طبقات الشبكة وبروتوكولاتها.",
    upcomingAssignments: [
      {
        title: "Exercise 1 (1st week)",
        dueDate: "السبت، 10 أكتوبر 2026 - 00:00",
        path: "DataCom/exercise1_diagram_final.png",
        status: "urgent"
      }
    ],
    socialLinks: [
      { type: "whatsapp", label: "مجموعة الواتس للطلاب (Male)", url: "https://chat.whatsapp.com/Iwir92UKIplGHrdNHfIQAG", note: "جروب المادة الرسمي للطلاب" },
      { type: "whatsapp", label: "مجموعة الواتس للطالبات (Female)", url: "https://chat.whatsapp.com/LJMh0A993ec2DZbMB0qsqk", note: "جروب المادة الرسمي للطالبات" }
    ],
    sections: [
      {
        title: "Course Description, Fall 2026",
        icon: "clipboard-list",
        items: [
          { title: "Syllabus Fall 26 (الخطة الدراسية)", type: "docx", path: "DataCom/DataComSyll-26 Fall.docx" }
        ]
      },
      {
        title: "Exams & Assignments Fall 2026",
        icon: "file-edit",
        items: [
          { title: "Exercise 1 (1st week) - التكليف الأول", type: "assignment", path: "DataCom/exercise1_diagram_final.png", badge: "مهم ومستحق" }
        ]
      },
      {
        title: "Introduction",
        icon: "folder",
        items: [
          { title: "Ch 1 - سلايدات الفصل الأول", type: "ppt", path: "DataCom/ch01-F.ppt" },
          { title: "ch1_pdf - ملف الفصل الأول PDF", type: "pdf", path: "DataCom/ch1.pdf" },
          { title: "Lecture_1A_Video - المحاضرة الأولى (الجزء A)", type: "video", path: "https://www.youtube.com/watch?v=JMlJxjJT4Wk" },
          { title: "Lecture_1B_Video - المحاضرة الأولى (الجزء B)", type: "video", path: "https://www.youtube.com/watch?v=AB48Q-u80ss" },
          { title: "lecture_1C - المحاضرة الأولى (الجزء C)", type: "video", path: "https://www.youtube.com/watch?v=tupOVIlgttw&t=3s" }
        ]
      },
      {
        title: "Network Models",
        icon: "folder",
        items: [
          { title: "Ch 2 - ملف الفصل الثاني PDF", type: "pdf", path: "DataCom/ch2.pdf" },
          { title: "lec2A - محاضرة الفصل الثاني (الجزء A)", type: "video", path: "https://www.youtube.com/watch?v=ovY1K3wWYSE" },
          { title: "lec2B - محاضرة الفصل الثاني (الجزء B)", type: "video", path: "https://www.youtube.com/watch?v=XaL4mxbsBiw" },
          { title: "Chapter 2 - سلايدات الفصل الثاني", type: "ppt", path: "DataCom/ch02-F.ppt" }
        ]
      },
      {
        title: "Chapter 3: Data and Signals",
        icon: "folder",
        items: [
          { title: "Ch 3 - ملف الفصل الثالث PDF", type: "pdf", path: "DataCom/ch3.pdf" },
          { title: "Chapter 3 - سلايدات الفصل الثالث", type: "ppt", path: "DataCom/ch03-FF.ppt" }
        ,
          { title: "Phys L 1 - مقدمة الطبقة المادية", type: "video", path: "https://www.youtube.com/watch?v=Km_nj8mdCzU" },
          { title: "dig tr 1 - الإرسال الرقمي 1", type: "video", path: "https://www.youtube.com/watch?v=L-LyRAk5N2U" },
          { title: "Dig tr 2 - الإرسال الرقمي 2", type: "video", path: "https://www.youtube.com/watch?v=CRSffscnB0Y" },
          { title: "Dig tr 3 - الإرسال الرقمي 3", type: "video", path: "https://www.youtube.com/watch?v=wf0edqUsgig" },
          { title: "Dig tr 4 - الإرسال الرقمي 4", type: "video", path: "https://www.youtube.com/watch?v=6a7Xtjo5HtI" },
          { title: "decibel - حسابات الديسيبل", type: "video", path: "https://www.youtube.com/watch?v=x-3o0LLvg9g" },
          { title: "Shannon - سعة القناة ونظرية شانون", type: "video", path: "https://www.youtube.com/watch?v=kTyKGZAWsOs" },
          { title: "ch3_Performance - مقاييس أداء الشبكة", type: "video", path: "https://www.youtube.com/watch?v=b8z5uY7QSGg" }]
      }
          {
        title: "Chapter 26",
        icon: "folder",
        items: [
          { title: "لقاء 1 أونلاين طالبات 2026", type: "video", path: "https://youtu.be/0ZSClkep7OQ?si=IXSTpQVC_rrBcZOX" }
        ]
      },
          {
        title: "Chapter 26",
        icon: "folder",
        items: [
          { title: "لقاء 1 أونلاين طلاب 2026", type: "link", path: "https://drive.google.com/file/d/1XqJJLI3XDZKD2_awODvp2-CZUleZ9tEd/view?usp=sharing" }
        ]
      },
    ]
  },
  {
    id: "os",
    code: "ECOM4401-6276",
    pageUrl: "course-os.html",
    title: "نظم تشغيل",
    englishTitle: "Operating Systems",
    category: "theory",
    semester: "خريف 2026 (Fall 2026)",
    icon: "cpu",
    description: "دراسة معمارية نظم التشغيل الحديثة، إدارة العمليات والذاكرة والجدولة والخيوط المتزامنة (Threads).",
    upcomingAssignments: [],
    socialLinks: [
      { type: "whatsapp", label: "مجموعة الواتساب (للطلاب Male)", url: "https://chat.whatsapp.com/IwFDiWMEuZrLXPuCmhSsqD", note: "جروب المادة الرسمي للطلاب" },
      { type: "whatsapp", label: "مجموعة الواتساب (للطالبات Female)", url: "https://chat.whatsapp.com/GRU8TeY3rNh8iMNT1exmuA", note: "جروب المادة الرسمي للطالبات" }
    ],
    sections: [
      {
        title: "General (معلومات عامة والخطة والكتاب)",
        icon: "clipboard-list",
        items: [
          { title: "Operating Systems Syllabus (الخطة الدراسية)", type: "pdf", path: "OS/Operating_Systems_Syllabus.pdf" },
          { title: "Syllabus Video - فيديو شرح الخطة", type: "video", path: "https://www.youtube.com/watch?v=LNy0qySddHM" },
          { title: "BookOS - الكتاب المعتمد للمقرر (Silberschatz)", type: "pdf", path: "OS/BookOS.pdf" }
        ]
      },
      {
        title: "Chapter 1: Introduction",
        icon: "folder",
        items: [
          { title: "Lecture 2 part 2, Chapter 1", type: "video", path: "https://youtu.be/OtG3wOwrNnM" },
          { title: "Lecture 2 part 1, Chapter 1:  Storage Structure &amp;amp; Multiprogramming.", type: "video", path: "https://youtu.be/vp9Bj8Lttlo" },
          { title: "Chapter 1: Introduction - سلايدات الفصل الأول", type: "ppt", path: "OS/ch1.pptx" },
          { title: "Chapter 1: Introduction, Lecture 1 part 1 - تسجيل المحاضرة الأولى (الجزء 1)", type: "video", path: "https://www.youtube.com/watch?v=UKrWWFVM6uM" },
          { title: "Chapter 1: Introduction, Lecture 1 part 2 - تسجيل المحاضرة الأولى (الجزء 2)", type: "video", path: "https://youtu.be/wL8bLp2fkc0" }
        ]
      },
      {
        title: "Chapter 2: Operating-System Services & Structures",
        icon: "folder",
        items: [
          { title: "Chapter 2: Operating-System Services - سلايدات الفصل الثاني", type: "ppt", path: "OS/ch2.pptx" }
        ]
      },
      {
        title: "Chapter 3: Processes",
        icon: "folder",
        items: [
          { title: "Chapter 3: Processes - سلايدات الفصل الثالث", type: "ppt", path: "OS/ch3.pptx" }
        ]
      },
      {
        title: "Chapter 4: Threads & Concurrency",
        icon: "folder",
        items: [
          { title: "Chapter 4: Threads & Concurrency - سلايدات الفصل الرابع", type: "ppt", path: "OS/ch4.pptx" }
        ]
      },
      {
        title: "Chapter 5: CPU Scheduling",
        icon: "folder",
        items: [
          { title: "Chapter 5: CPU Scheduling - سلايدات الفصل الخامس", type: "ppt", path: "OS/ch5.pptx" }
        ]
      },
      {
        title: "Chapter 6: Synchronization Tools",
        icon: "folder",
        items: [
          { title: "Chapter 6: Synchronization Tools - سلايدات الفصل السادس", type: "ppt", path: "OS/ch6.pptx" }
        ]
      },
      {
        title: "Chapter 7: Synchronization Examples",
        icon: "folder",
        items: [
          { title: "Chapter 7: Synchronization Examples - سلايدات الفصل السابع", type: "ppt", path: "OS/ch7.pptx" }
        ]
      },
      {
        title: "Chapter 8: Deadlocks",
        icon: "folder",
        items: [
          { title: "Chapter 8: Deadlocks - سلايدات الفصل الثامن", type: "ppt", path: "OS/ch8.pptx" }
        ]
      },
      {
        title: "Chapter 9: Main Memory",
        icon: "folder",
        items: [
          { title: "Chapter 9: Main Memory - سلايدات الفصل التاسع", type: "ppt", path: "OS/ch9.pptx" }
        ]
      },
      {
        title: "Chapter 10: Virtual Memory",
        icon: "folder",
        items: [
          { title: "Chapter 10: Virtual Memory - سلايدات الفصل العاشر", type: "ppt", path: "OS/ch10.pptx" }
        ]
      },
      {
        title: "Chapter 13: File-System Interface",
        icon: "folder",
        items: [
          { title: "Chapter 13: File-System Interface - سلايدات الفصل الثالث عشر", type: "ppt", path: "OS/ch13.pptx" }
        ]
      },
      {
        title: "Chapter 16: Security",
        icon: "folder",
        items: [
          { title: "Chapter 16: Security - سلايدات الفصل السادس عشر", type: "ppt", path: "OS/ch16.pptx" }
        ]
      },
      {
        title: "Chapter 18: Virtual Machines",
        icon: "folder",
        items: [
          { title: "Chapter 18: Virtual Machines - سلايدات الفصل الثامن عشر", type: "ppt", path: "OS/ch18.pptx" }
        ]
      }
    ]
  },
  {
    id: "assembly",
    code: "ECOM4403-2463",
    pageUrl: "course-assembly.html",
    title: "تنظيم حاسوب ولغة أسمبلي",
    englishTitle: "Computer Organization and Assembly Language",
    category: "theory",
    semester: "خريف 2026 (Fall 2026)",
    icon: "binary",
    description: "بنية المعالج x86، السجلات، لغة التجميع من الصفر، إدارة الذاكرة، التعليمات والبرمجة منخفضة المستوى.",
    upcomingAssignments: [],
    socialLinks: [
      { type: "whatsapp", label: "مجموعة الواتس للطلاب (Male)", url: "https://chat.whatsapp.com/KoCgKTG0rc3BlvyUvVbA8w", note: "جروب المادة الرسمي للطلاب" },
      { type: "whatsapp", label: "مجموعة الواتس للطالبات (Female)", url: "#", note: "خاص بطالبات الشعبة الرسمية" }
    ],
    sections: [
      {
        title: "Course Information (معلومات المقرر والكتب والخطة)",
        icon: "clipboard-list",
        items: [
          { title: "assembly Syllabus 2025_2026 (الخطة الدراسية للمقرر)", type: "pdf", path: "Assembly/assembly Syllabus 2025_2026.pdf" },
          { title: "TextBook - الكتاب المعتمد للمقرر (Kip Irvine)", type: "link", path: "https://drive.google.com/file/d/1xD533nMjzSshzW5SSUBs0NmCaQmr-Efd/view?usp=sharing" },
          { title: "lecture0_Course-Information - المحاضرة التمهيدية", type: "ppt", path: "Assembly/lecture0_Course-Information.pptx" },
          { title: "CourseInformation Video - فيديو شرح خطة ومقدمة المادة", type: "video", path: "https://www.youtube.com/watch?v=8dz6RgIJhSg" }
        ]
      },
      {
        title: "Chapter 1: Basic Concepts (المفاهيم الأساسية)",
        icon: "folder",
        items: [
          { title: "01-BasicConcepts - سلايدات الفصل الأول", type: "ppt", path: "Assembly/01-BasicConcepts.pptx" },
          { title: "Chapter1_Lecture - فيديو المحاضرة الأولى", type: "video", path: "https://www.youtube.com/watch?v=SWLzb2xuBZE" }
        ]
      },
      {
        title: "Chapter 2: Processor Architecture & Execution Cycle",
        icon: "film",
        items: [
          { title: "FetchDecodeExcute Cycle - فيديو دورة الجلب والتنفيذ", type: "video", path: "Assembly/FetchDecodeExcute.mp4" }
        ,
          { title: "Chapter 2: Lecture 1 - معمارية المعالج", type: "video", path: "https://youtu.be/-NJxlwUl8lM" },
          { title: "Chapter 2: Lecture 2 - معمارية المعالج", type: "video", path: "https://youtu.be/bpNRf2F7gvI" }]
      },
      {
        title: "Chapter 3: Assembly Language Fundamentals",
        icon: "folder",
        items: [
          { title: "Chapter3AssemblyLanguageFundamentals - ملف الفصل الثالث", type: "pdf", path: "Assembly/Chapter3AssemblyLanguageFundamentals.pdf" },
          { title: "Chapter3_Lecture#2 - تسجيل المحاضرة الثانية", type: "video", path: "https://drive.google.com/file/d/1at03W_r_bN6KofpFYHSAGCGzY0fKl9_s/view" }
        ]
      }
    ]
  },
  {
    id: "data_comm_lab",
    code: "ECOM4002-6439",
    pageUrl: "course-datacom-lab.html",
    title: "اتصالات بيانات (عملي)",
    englishTitle: "Data Communications Lab",
    category: "lab",
    semester: "خريف 2026 (Fall 2026)",
    icon: "network",
    description: "تطبيقات وتجارب شبكات الحاسوب، كابلات الشبكة، محاكاة Cisco Packet Tracer، تحليل الحزم عبر Wireshark.",
    upcomingAssignments: [],
    socialLinks: [
      { type: "whatsapp", label: "مجموعة الواتس لمعمل الاتصالات", url: "https://chat.whatsapp.com/CRbZGiixjU96D5cDrSUR4F", note: "جروب المعمل الرسمي للمناقشة والتسليمات" }
    ],
    sections: [
      {
        title: "Lab 1: تجارب المعمل",
        icon: "flask-conical",
        items: [
          { title: "Lab 1 - تسجيل وتجربة المعمل الأولى", type: "video", path: "https://www.youtube.com/watch?v=2DI0YVuM5nA&list=PLVrdY3SfDg98" },
          { title: "Lab 1 - أساسيات اتصالات البيانات وشبكات الحاسوب (Fundamentals of Data Communications)", type: "pdf", path: "DataCom/lab1__Fundamentals_of_data_communications_and_computer_networks.pdf" }
        ]
      },
    ]
  },
  {
    id: "os_lab",
    code: "ECOM4001-6436",
    pageUrl: "course-os-lab.html",
    title: "نظم تشغيل (عملي)",
    englishTitle: "Operating Systems Lab",
    category: "lab",
    semester: "خريف 2026 (Fall 2026)",
    icon: "terminal",
    description: "البرمجة العملية لنظم التشغيل باستخدام Linux Bash Shell و C / System Calls (Fork, Threads, IPC).",
    upcomingAssignments: [],
    socialLinks: [
      { type: "whatsapp", label: "مجموعة الواتساب لمعمل نظم التشغيل", url: "https://chat.whatsapp.com/Hk7qiaE1K8gJd4CJ16umQi", note: "متابعة المهام والتسليمات العملية" }
    ],
    sections: []
  },
  {
    id: "assembly_lab",
    code: "ECOM4003-6427",
    pageUrl: "course-assembly-lab.html",
    title: "لغة تجميع (عملي)",
    englishTitle: "Assembly Language Lab",
    category: "lab",
    semester: "خريف 2026 (Fall 2026)",
    icon: "circuit-board",
    description: "التطبيق العملي وكتابة كود الأسمبلي باستخدام أدوات TASM و DOSBox و EMU8086، وتتبع السجلات والذاكرة.",
    upcomingAssignments: [],
    socialLinks: [
      { type: "whatsapp", label: "مجموعة الواتساب لمعمل لغة التجميع", url: "https://chat.whatsapp.com/KSehBCCLCkAElrUYeHKbXp", note: "جروب المعمل الرسمي للمناقشة" }
    ],
    sections: [
      {
        title: "Lab 0: تجارب المعمل",
        icon: "flask-conical",
        items: [
          { title: "Lab 00 - Lecture", type: "video", path: "https://youtu.be/H_23IYTr3bg" },
          { title: "Visual Studio Download", type: "link", path: "https://visualstudio.microsoft.com/" },
          { title: "Assembly Lab 0", type: "pdf", path: "Assembly/Assembly Lab_0.pdf" }
        ]
      },
    ]
  }
];

if (typeof window !== 'undefined') {
  window.COURSES_DATA = COURSES_DATA;
}
