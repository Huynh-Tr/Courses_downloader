# 📚 DANH MỤC KHÓA HỌC ĐÃ TẢI VỀ (COURSES DATABASE)

> **Cập nhật lần cuối:** 2026-10-06  
> **Lưu trữ chính:** `/mnt/gdrive/Learning/`  
> **Quản lý công cụ tải:** `/home/ubuntu/Courses_downloader/`  
> **Nền tảng hỗ trợ:** Coursera, edX, MITx Online  
> **Trạng thái:** Toàn bộ 48 khóa học dưới đây đã tải hoàn tất và đồng bộ lên Google Drive.

---

## ⚠️ QUY TẮC BẮT BUỘC TRƯỚC KHI TẢI KHÓA HỌC (PRE-DOWNLOAD PROTOCOL)

Mỗi khi người dùng yêu cầu tải bất kỳ khóa học nào (Coursera, edX, MITx Online), **Claude Code / Agent PHẢI thực hiện theo quy trình 3 bước sau**:

1. **BƯỚC 1: TRA CỨU TRÁNH TẢI TRÙNG**
   - Tìm kiếm slug, mã khóa học (course code), hoặc tên khóa học trong file `courses.md` này:
     ```bash
     grep -i "<slug-hoặc-tên-khóa>" /home/ubuntu/Courses_downloader/courses.md
     ```
   - Hoặc kiểm tra trực tiếp thư mục Google Drive:
     ```bash
     ls -d /mnt/gdrive/Learning/Coursera/*/*<slug>* 2>/dev/null
     ls -d /mnt/gdrive/Learning/Edx/*<code-hoặc-tên>* 2>/dev/null
     ls -d /mnt/gdrive/Learning/MIT/*<code-hoặc-tên>* 2>/dev/null
     ```

2. **BƯỚC 2: PHẢN HỒI NẾU ĐÃ CÓ**
   - Nếu khóa học **ĐÃ CÓ** trong danh sách:
     - ❌ **KHÔNG ĐƯỢC TẢI LẠI** (tránh lãng phí băng thông, thời gian và dung lượng lưu trữ).
     - 📢 Báo ngay cho người dùng: Khóa học đã được tải hoàn tất, cung cấp đường dẫn thư mục tương ứng trên Google Drive (`/mnt/gdrive/Learning/...`) và chi tiết số lượng file/bài học.

3. **BƯỚC 3: TẢI & CẬP NHẬT NẾU CHƯA CÓ**
   - Nếu khóa học **CHƯA CÓ**: Tiến hành tải bằng công cụ phù hợp:
     - Coursera: `queue_manager.py` hoặc `coursera-dl`
     - edX: `edx-batch` (`edx_downloader.py`) hoặc `edx-dl`
     - MITx Online: `mit-dl` (`mit_downloader.py`)
   - **Sau khi tải thành công:** Ngay lập tức cập nhật thông tin khóa học mới (Slug, Tên, Số file, Dung lượng, Đường dẫn) vào file `courses.md` này!

---

## 📊 THỐNG KÊ TỔNG QUAN

| Nền tảng | Số khóa học | Chuyên ngành / Đơn vị đào tạo | Quy mô & Dung lượng ước tính |
| :--- | :---: | :--- | :---: |
| **Coursera** | 30 | 7 Specializations (Wharton, Northwestern, Penn) | ~28 GB (45,000+ files) |
| **edX** | 7 | Stanford Online, UC Berkeley (BerkeleyX), MITx | ~19 GB (1,000+ files) |
| **MIT (MITx & OCW)** | 11 | MIT Sloan MicroMasters in Finance & OCW | ~32.3 GB (1,380+ files) |
| **TỔNG CỘNG** | **48** | **Wharton, Stanford, UC Berkeley, MIT Sloan, Northwestern, Penn** | **~79.3 GB (47,380+ files)** |

---

## 🗂️ BẢNG TRA CỨU NHANH (QUICK LOOKUP)

### 1. Coursera (30 khóa)

| STT | Course Slug | Tên Khóa Học | Chuyên Ngành (Specialization) | Files | Size | Trạng thái |
|:---:|:---|:---|:---|:---:|:---:|:---:|
| 1 | `finance-healthcare-managers` | Finance for Healthcare Managers | Finance & Quantitative Modeling | 1,660 | 470 MB | ✅ COMPLETED |
| 2 | `wharton-finance` | Introduction to Corporate Finance | Finance & Quantitative Modeling | 824 | 302 MB | ✅ COMPLETED |
| 3 | `positive-psychology-visionary-science` | Martin Seligman's Visionary Science | Positive Psychology | 3,907 | 6.3 GB | ✅ COMPLETED |
| 4 | `positive-psychology-applications` | Applications and Interventions | Positive Psychology | 4,708 | 2.0 GB | ✅ COMPLETED |
| 5 | `positive-psychology-methods` | Character, Grit and Research Methods | Positive Psychology | 3,807 | 1.8 GB | ✅ COMPLETED |
| 6 | `positive-psychology-resilience` | Resilience Skills in a Time of Uncertainty | Positive Psychology | 6,006 | 4.1 GB | ✅ COMPLETED |
| 7 | `positive-psychology-project` | Positive Psychology Specialization Project | Positive Psychology | 1,729 | 1.3 GB | ✅ COMPLETED |
| 8 | `team-culture` | Leadership and Team Culture | High Performance Collaboration | 2,818 | 537 MB | ✅ COMPLETED |
| 9 | `high-performing-teams` | Creating and Leading High-Performing Teams | High Performance Collaboration | 2,023 | 469 MB | ✅ COMPLETED |
| 10 | `diverse-teams` | Collaborating in Diverse Teams | High Performance Collaboration | 2,242 | 535 MB | ✅ COMPLETED |
| 11 | `continuous-learning-culture` | Creating a Culture of Continuous Learning | High Performance Collaboration | 2,114 | 713 MB | ✅ COMPLETED |
| 12 | `team-building-capstone` | High Performance Collaboration Capstone | High Performance Collaboration | 1,598 | 388 MB | ✅ COMPLETED |
| 13 | `wharton-customer-analytics` | Customer Analytics | Wharton Business Analytics | 2,337 | 768 MB | ✅ COMPLETED |
| 14 | `wharton-operations-analytics` | Operations Analytics | Wharton Business Analytics | 1,286 | 668 MB | ✅ COMPLETED |
| 15 | `wharton-people-analytics` | People Analytics | Wharton Business Analytics | 2,275 | 680 MB | ✅ COMPLETED |
| 16 | `accounting-analytics` | Accounting Analytics | Wharton Business Analytics | 1,822 | 689 MB | ✅ COMPLETED |
| 17 | `wharton-capstone-analytics` | Business Analytics Capstone | Wharton Business Analytics | 1,524 | 550 MB | ✅ COMPLETED |
| 18 | `wharton-quantitative-modeling` | Fundamentals of Quantitative Modeling | Wharton Business & Financial Modeling | 1,899 | 422 MB | ✅ COMPLETED |
| 19 | `wharton-introduction-spreadsheets-models` | Introduction to Spreadsheets and Models | Wharton Business & Financial Modeling | 1,287 | 416 MB | ✅ COMPLETED |
| 20 | `wharton-risk-models` | Modeling Risk and Realities | Wharton Business & Financial Modeling | 901 | 351 MB | ✅ COMPLETED |
| 21 | `wharton-decision-making-scenarios` | Decision-Making and Scenarios | Wharton Business & Financial Modeling | 1,196 | 361 MB | ✅ COMPLETED |
| 22 | `wharton-business-financial-modeling-capstone` | Business & Financial Modeling Capstone | Wharton Business & Financial Modeling | 981 | 359 MB | ✅ COMPLETED |
| 23 | `wharton-global-trends-business` | Global Trends for Business and Society | Wharton Global Business Strategy | 1,529 | 618 MB | ✅ COMPLETED |
| 24 | `wharton-corruption` | Corruption: Global Business & Policy | Wharton Global Business Strategy | 808 | 418 MB | ✅ COMPLETED |
| 25 | `wharton-social-entrepreneurship` | Social Entrepreneurship | Wharton Global Business Strategy | 720 | 294 MB | ✅ COMPLETED |
| 26 | `wharton-social-impact` | Global Business and Social Impact | Wharton Global Business Strategy | 2,054 | 880 MB | ✅ COMPLETED |
| 27 | `wharton-success` | Success: What is Success? | Wharton Success | 1,589 | 638 MB | ✅ COMPLETED |
| 28 | `wharton-communication-skills` | Improving Communication Skills | Wharton Success | 2,223 | 501 MB | ✅ COMPLETED |
| 29 | `wharton-influence` | Influence: How to Lead Without Authority | Wharton Success | 2,857 | 764 MB | ✅ COMPLETED |
| 30 | `wharton-online-negotiations` | Negotiations: How to Win Without Conflict | Wharton Success | 1,342 | 742 MB | ✅ COMPLETED |

---

### 2. edX (7 khóa)

| STT | Course Code | Tên Khóa Học | Trường Đào Tạo | Files | Size | Trạng thái |
|:---:|:---|:---|:---|:---:|:---:|:---:|
| 1 | `SOHS-YSTATSLEARNINGP` | Statistical Learning with Python | Stanford Online | 230 | 3.8 GB | ✅ COMPLETED |
| 2 | `CSX0002` | Mining Massive Datasets | Stanford Online | 187 | 1.8 GB | ✅ COMPLETED |
| 3 | `ColWri2.1x` | How to Write an Essay | UC Berkeley (BerkeleyX) | 11 | 37 MB | ✅ COMPLETED |
| 4 | `Data88.1EX` | Fundamentals of Economics | UC Berkeley (BerkeleyX) | 23 | 614 MB | ✅ COMPLETED |
| 5 | `Data88.2EX` | Advanced Concepts in Economics | UC Berkeley (BerkeleyX) | 25 | 784 MB | ✅ COMPLETED |
| 6 | `Data88.3EX` | Real-World Applications of Economics | UC Berkeley (BerkeleyX) | 17 | 557 MB | ✅ COMPLETED |
| 7 | `MITx-15.481x` (1T2021) | Adaptive Markets: Financial Market Dynamics | MITx / edX | 536 | 11.2 GB | ✅ COMPLETED |

---

### 3. MIT (MITx Online & OpenCourseWare - 12 khóa)

| STT | Course Code | Tên Khóa Học | Học Viện / Chương Trình | Files | Size | Trạng thái |
|:---:|:---|:---|:---|:---:|:---:|:---:|
| 1 | `15.415.1x` | Foundations of Modern Finance I | MIT Sloan MicroMasters in Finance | 393 | 13.5 GB | ✅ COMPLETED |
| 2 | `15.415.2x` | Foundations of Modern Finance II | MIT Sloan MicroMasters in Finance | 297 | 2.7 GB | ✅ COMPLETED |
| 3 | `15.435x` | Derivatives Markets: Advanced Modeling | MIT Sloan MicroMasters in Finance | 255 | 11.6 GB | ✅ COMPLETED |
| 4 | `15.455x` | Mathematical Methods for Quantitative Finance | MIT Sloan MicroMasters in Finance | 271 | 4.9 GB | ✅ COMPLETED |
| 5 | `15.450` | Analytics of Finance (Fall 2010) | MIT Sloan / Prof. Leonid Kogan | 51 | 49.7 MB | ✅ COMPLETED |
| 6 | `15.483` | Consumer Finance: Markets, Product Design, and Fintech (Spring 2018) | MIT Sloan / Prof. Jonathan Parker | 20 | 45.8 MB | ✅ COMPLETED |
| 7 | `15.521` | Management Accounting and Control (Spring 2003) | MIT Sloan / Prof. Joseph Weber | 27 | 11.8 MB | ✅ COMPLETED |
| 8 | `15.S08` | FinTech: Shaping the Financial World (Spring 2020) | MIT Sloan / Prof. Gary Gensler | 76 | 41.0 MB | ✅ COMPLETED |
| 9 | `15.414` | Financial Management (Summer 2003) | MIT Sloan / Prof. Jonathan Lewellen | 46 | 56.6 MB | ✅ COMPLETED |
| 10 | `14.01` | Principles of Microeconomics (Fall 2023) | MIT Economics / Prof. Jonathan Gruber | 130 | 71.5 MB | ✅ COMPLETED |
| 11 | `15.997` | Practice of Finance: Advanced Corporate Risk Management (Spring 2009) | MIT Sloan / Prof. John Parsons | 38 | 77.4 MB | ✅ COMPLETED |
| 12 | `14.02` | Principles of Macroeconomics (Spring 2023) | MIT Economics / Prof. Ricardo Caballero | 80 | 29.1 MB | ✅ COMPLETED |

---

## 📁 CHI TIẾT ĐƯỜNG DẪN LƯU TRỮ VÀ CẤU TRÚC FOLDER

### 1. Coursera (`/mnt/gdrive/Learning/Coursera/`)

#### 1.1. Finance and Quantitative Modeling for Analysts
- **Đường dẫn chuyên ngành:** `/mnt/gdrive/Learning/Coursera/Finance and Quantitative Modeling for Analysts/`
  1. `finance-healthcare-managers/` (1,660 files, 470.1 MB)
  2. `wharton-finance/` (824 files, 301.9 MB)

#### 1.2. Positive Psychology Specialization
- **Đường dẫn chuyên ngành:** `/mnt/gdrive/Learning/Coursera/Positive Psychology/`
  1. `positive-psychology-visionary-science/` (3,907 files, 6.35 GB)
  2. `positive-psychology-applications/` (4,708 files, 2.03 GB)
  3. `positive-psychology-methods/` (3,807 files, 1.84 GB)
  4. `positive-psychology-resilience/` (6,006 files, 4.13 GB)
  5. `positive-psychology-project/` (1,729 files, 1.34 GB)

#### 1.3. High Performance Collaboration: Leadership, Teamwork, and Negotiation
- **Đường dẫn chuyên ngành:** `/mnt/gdrive/Learning/Coursera/Team Building/`
  1. `team-culture/` (2,818 files, 536.5 MB)
  2. `high-performing-teams/` (2,023 files, 468.7 MB)
  3. `diverse-teams/` (2,242 files, 534.9 MB)
  4. `continuous-learning-culture/` (2,114 files, 713.2 MB)
  5. `team-building-capstone/` (1,598 files, 388.1 MB)

#### 1.4. Wharton Business Analytics Specialization
- **Đường dẫn chuyên ngành:** `/mnt/gdrive/Learning/Coursera/Wharton Business Analytics/`
  1. `wharton-customer-analytics/` (2,337 files, 768.3 MB)
  2. `wharton-operations-analytics/` (1,286 files, 668.3 MB)
  3. `wharton-people-analytics/` (2,275 files, 679.9 MB)
  4. `accounting-analytics/` (1,822 files, 689.2 MB)
  5. `wharton-capstone-analytics/` (1,524 files, 550.4 MB)

#### 1.5. Wharton Business and Financial Modeling Specialization
- **Đường dẫn chuyên ngành:** `/mnt/gdrive/Learning/Coursera/Wharton Business and Financial Modeling/`
  1. `wharton-quantitative-modeling/` (1,899 files, 422.3 MB)
  2. `wharton-introduction-spreadsheets-models/` (1,287 files, 416.0 MB)
  3. `wharton-risk-models/` (901 files, 350.8 MB)
  4. `wharton-decision-making-scenarios/` (1,196 files, 361.4 MB)
  5. `wharton-business-financial-modeling-capstone/` (981 files, 358.8 MB)

#### 1.6. Wharton Global Business Strategy Specialization
- **Đường dẫn chuyên ngành:** `/mnt/gdrive/Learning/Coursera/Wharton Global Business Strategy/`
  1. `wharton-global-trends-business/` (1,529 files, 618.3 MB)
  2. `wharton-corruption/` (808 files, 418.1 MB)
  3. `wharton-social-entrepreneurship/` (720 files, 294.2 MB)
  4. `wharton-social-impact/` (2,054 files, 880.3 MB)

#### 1.7. Wharton Achieving Personal and Professional Success Specialization
- **Đường dẫn chuyên ngành:** `/mnt/gdrive/Learning/Coursera/Wharton Success/`
  1. `wharton-success/` (1,589 files, 637.6 MB)
  2. `wharton-communication-skills/` (2,223 files, 501.4 MB)
  3. `wharton-influence/` (2,857 files, 764.5 MB)
  4. `wharton-online-negotiations/` (1,342 files, 741.9 MB)

---

### 2. edX (`/mnt/gdrive/Learning/Edx/`)

1. **CSX0002 - Mining Massive Datasets**
   - Đường dẫn: `/mnt/gdrive/Learning/Edx/CSX0002 - Mining Massive Datasets`
   - Nội dung: 16 module (MapReduce, PageRank, Locality-Sensitive Hashing, Stream Mining, Link Analysis...)
   - Quy mô: 187 files (93 video, 93 transcript), 1.83 GB

2. **ColWri2.1x - How to Write an Essay**
   - Đường dẫn: `/mnt/gdrive/Learning/Edx/ColWri2.1x - How to Write an Essay`
   - Nội dung: 5 week (Grammar, Sentences, Paragraphs, Thesis Statements...)
   - Quy mô: 11 files (5 video, 5 transcript), 36.7 MB

3. **Data88.1EX - Fundamentals of Economics**
   - Đường dẫn: `/mnt/gdrive/Learning/Edx/Data88.1EX - Fundamentals of Economics`
   - Nội dung: 4 module (Demand, Supply, Government & Welfare...)
   - Quy mô: 23 files (11 video, 11 transcript), 614.1 MB

4. **Data88.2EX - Advanced Concepts in Economics**
   - Đường dẫn: `/mnt/gdrive/Learning/Edx/Data88.2EX - Advanced Concepts in Economics`
   - Nội dung: 4 module (Production & Macro Policy, Utility & LaTeX, Inequality & Development...)
   - Quy mô: 25 files (12 video, 12 transcript), 783.7 MB

5. **Data88.3EX - Real-World Applications of Economics**
   - Đường dẫn: `/mnt/gdrive/Learning/Edx/Data88.3EX - Real-World Applications of Economics`
   - Nội dung: 5 module (Game Theory, Econometrics, Environmental Economics...)
   - Quy mô: 17 files (8 video, 8 transcript), 556.7 MB

6. **MITx-15.481x-1T2021 - Adaptive Markets: Financial Market Dynamics and Human Behavior**
   - Đường dẫn: `/mnt/gdrive/Learning/Edx/MITx-15.481x-1T2021`
   - Giảng viên: Prof. Andrew Lo (MIT Sloan)
   - Nội dung: 13 unit (Financial Orthodoxy, Random Walk, Behavioral Biases, Neuroscience, Adaptive Markets Hypothesis...)
   - Quy mô: 536 files, 11.22 GB

7. **SOHS-YSTATSLEARNINGP - Statistical Learning with Python**
   - Đường dẫn: `/mnt/gdrive/Learning/Edx/SOHS-YSTATSLEARNINGP - Statistical Learning with Python`
   - Giảng viên: Trevor Hastie, Robert Tibshirani, Jonathan Taylor (Stanford)
   - Nội dung: 14 chương tương ứng giáo trình An Introduction to Statistical Learning (ISLP)
   - Quy mô: 230 files (115 video, 114 transcript), 3.85 GB

---

### 3. MITx Online (`/mnt/gdrive/Learning/MIT/`)

Toàn bộ 4 môn cốt lõi của chương trình danh giá **MIT Sloan MicroMasters in Finance**:

1. **15.415.1x - Foundations of Modern Finance I**
   - Đường dẫn: `/mnt/gdrive/Learning/MIT/15.415.1x - Foundations of Modern Finance I`
   - Nội dung: Time Value of Money, Fixed Income, Equities, Portfolio Theory, CAPM, Factor Models
   - Quy mô: 393 files (196 video, 196 transcript), 13.50 GB

2. **15.415.2x - Foundations of Modern Finance II**
   - Đường dẫn: `/mnt/gdrive/Learning/MIT/15.415.2x - Foundations of Modern Finance II`
   - Nội dung: Corporate Finance, Capital Budgeting, WACC, Capital Structure, Forwards/Futures, Options, Risk Management
   - Quy mô: 297 files, 2.75 GB

3. **15.435x - Derivatives Markets: Advanced Modeling and Strategies**
   - Đường dẫn: `/mnt/gdrive/Learning/MIT/15.435x - Derivatives Markets - Advanced Modeling and Strategies`
   - Nội dung: Forward Contracts, Futures & Swaps, Options, Black-Scholes Formula, Greeks & Hedging, Volatility Trading, Structured Products
   - Quy mô: 255 files, 11.56 GB

4. **15.455x - Mathematical Methods for Quantitative Finance**
   - Đường dẫn: `/mnt/gdrive/Learning/MIT/15.455x - Mathematical Methods for Quantitative Finance`
   - Nội dung: Probability Foundations, Discrete & Continuous Stochastic Processes, Linear Algebra, Optimization, Numerical Methods for Finance
   - Quy mô: 271 files, 4.86 GB

5. **15.450 - Analytics of Finance (Fall 2010)**
   - Đường dẫn: `/mnt/gdrive/Learning/MIT/15.450 - Analytics of Finance (Fall 2010)`
   - Giảng viên: Prof. Leonid Kogan (MIT Sloan School of Management)
   - Nội dung: Arbitrage-Free Pricing, Stochastic Calculus, Monte Carlo & Variance Reduction, Dynamic Portfolio Choice (Martingale approach), Dynamic Programming (HJB & Numerical DP), Financial Econometrics, GMM, Newey-West HAC, Stambaugh Bias & Bootstrap, Volatility Models (ARCH/GARCH, MIDAS)
   - Quy mô: 51 files (Lecture notes, Recitations, Problem sets, Final Exam & Solutions, MATLAB code, Canonical Research Papers, Textbooks), 49.67 MB

7. **15.521 - Management Accounting and Control (Spring 2003)**
   - Đường dẫn: `/mnt/gdrive/Learning/MIT/15.521 - Management Accounting and Control (Spring 2003)`
   - Giảng viên: Prof. Joseph Weber (MIT Sloan School of Management)
   - Nội dung: Managerial & Organizational Economics, Decision Rights & Responsibility Centers (Cost/Profit/Investment Centers), ROI/RI/EVA, Transfer Pricing, Budgeting & Horizon Problems, Cost Allocations (Direct, Step-down, Reciprocal), Absorption Costing & Death Spiral, Standard Costing & Variance Analysis, Activity-Based Costing (ABC), Balanced Scorecard, Capstone Case Weber's Customized Electronics
   - Quy mô: 27 files (Course zip archive, Lecture notes PDF, Syllabus, Readings catalog, Final Exam Case & Data), 11.82 MB

7. **15.483 - Consumer Finance: Markets, Product Design, and Fintech (Spring 2018)**
   - Đường dẫn: `/mnt/gdrive/Learning/MIT/15.483 - Consumer Finance Markets Product Design and Fintech (Spring 2018)`
   - Giảng viên: Prof. Jonathan Parker (Robert C. Merton Professor of Finance, MIT Sloan School of Management)
   - Nội dung: Household Finance, Rational Life-Cycle Consumption Smoothing, Behavioral Biases (Present Bias, Hyperbolic Discounting, Mental Accounting), Financial Coaching & Health Checks (ideas42), Consumer Credit & Card Markets (Risk-based pricing, Adverse Selection & Market Unraveling, Citi Case), Microinsurance (BASIX India), P2P Marketplace Lending (Lending Club, WebBank charter, SEC Promissory Notes), Debt Securitization & CLO Tranche Modeling, Cryptocurrencies & Payment Systems (Bitcoin, Alipay, M-Pesa).
   - Quy mô: 20 files (Lecture notes, Case assignments, Excel CLO modeling sheet, Textbooks, Readings), 45.8 MB

8. **15.S08 - FinTech: Shaping the Financial World (Spring 2020)**
   - Đường dẫn: `/mnt/gdrive/Learning/MIT/15.S08 - FinTech - Shaping the Financial World (Spring 2020)`
   - Giảng viên: Prof. Gary Gensler (MIT Sloan School of Management, Former CFTC Chair, later SEC Chair)
   - Nội dung: FinTech Landscape & Trends, AI/ML/Deep Learning in Finance, Natural Language Processing & Chatbots, Open Banking & APIs, Robotic Process Automation (RPA), Blockchain Technology & Cryptocurrencies, Retail CBDC, Payment Rails & Digital Wallets (Alipay, WeChat Pay, Stripe, Plaid), Credit & P2P Marketplace Lending, Challenger Banks & Neobanks, Algorithmic Trading & Robo-advisors (Robinhood, Charles Schwab), InsurTech Value Chain, COVID-19 Financial Crisis & Policy Impact.
   - Quy mô: 76 files (Course Site Archive, Lecture Slides PDF, Transcripts, Canon Papers & Readings, Textbooks), 40.97 MB

---

9. **15.414 - Financial Management (Summer 2003)**
   - Đường dẫn: `/mnt/gdrive/Learning/MIT/15.414 - Financial Management (Summer 2003)`
   - Giảng viên: Prof. Jonathan Lewellen (MIT Sloan School of Management)
   - Nội dung: Principles of Valuation, Net Present Value (NPV), Real Options, Internal Rate of Return (IRR), Project & Firm Valuation (DCF, APV, Multiples), Free Cash Flows (FCF), Risk & Return Foundations, Modern Portfolio Theory (Markowitz Mean-Variance), Capital Asset Pricing Model (CAPM), Cost of Capital & Discount Rates in Practice, Raising Capital (IPOs, SEOs, Private Equity), Capital Structure & Financing Policy (Modigliani-Miller Theorems I & II, Trade-off Theory, Pecking Order Theory), Market Efficiency & Behavioral Finance, Options & Corporate Applications (Black-Scholes, Binomial Trees).
   - Quy mô: 46 files (Course archive zip, 17 Lecture slides, 7 Recitations, 7 Problem sets & assignments, 6 Midterm & Final Exams, 3 Financial modeling Excel spreadsheets, Canonical Textbooks: Brealey-Myers-Allen Corporate Finance & Bodie-Kane-Marcus Investments), 56.6 MB

10. **14.01 - Principles of Microeconomics (Fall 2023)**
   - Đường dẫn: `/mnt/gdrive/Learning/MIT/14.01 - Principles of Microeconomics (Fall 2023)`
   - Giảng viên: Prof. Jonathan Gruber (Ford Professor of Economics, MIT Department of Economics)
   - Nội dung: Consumer Theory (Preferences, Indifference Curves, Utility, Budget Constraint, Marginal Rate of Substitution, Constrained Optimization, Demand Curves, Income/Substitution Effects), Producer Theory (Production Functions, Marginal Product, MRTS, Cost Minimization, Short-run/Long-run Cost Curves), Perfect Competition (Firm & Market Supply, Short-run/Long-run Equilibrium, Welfare Economics, Consumer/Producer Surplus), Government Interventions & Deadweight Loss (Taxes, Subsidies, Price Ceilings/Floors, Tariffs, Quotas), Monopoly & Price Discrimination (1st, 2nd, 3rd Degree, Bundling, Natural Monopoly, Antitrust), Oligopoly & Game Theory (Cournot, Bertrand, Stackelberg, Nash Equilibrium, Prisoner's Dilemma), Factor Markets (Labor Supply & Demand, Minimum Wage, Capital Markets), Risk & Uncertainty (Expected Utility, Risk Aversion, Insurance Markets, Asymmetric Information, Adverse Selection, Moral Hazard), Market Failures (Externalities, Coase Theorem, Pigouvian Taxes/Subsidies, Cap-and-Trade, Public Goods, Free-rider Problem), Behavioral Economics (Bounded Rationality, Prospect Theory, Present Bias, Hyperbolic Discounting, Nudge).
   - Quy mô: 130 files (Course archive zip, 25 Lecture slide decks, 24 Lecture handouts & study guides, 26 Video transcripts & captions, 8 Problem sets & official full solutions, Midterm & Final Exams with solutions, Canonical Textbook: Jeffrey M. Perloff - Microeconomics 7th Edition), 71.5 MB

11. **15.997 - Practice of Finance: Advanced Corporate Risk Management (Spring 2009)**
   - Đường dẫn: `/mnt/gdrive/Learning/MIT/15.997 - Practice of Finance - Advanced Corporate Risk Management (Spring 2009)`
   - Giảng viên: Prof. John Parsons (MIT Sloan School of Management)
   - Nội dung: The Role of Risk Management (How & Why Companies Manage Risk, Shareholder Value vs Modigliani-Miller, Costs of Financial Distress, Debt Overhang, Underinvestment), Risk Measurement & Exposure (Exposure-based Cash-Flow-at-Risk, Dynamic Models), Dynamic Stochastic Models (Binomial Tree & Geometric Brownian Motion, Volatility & Drift), Risk-Neutral Pricing & Valuation of Real Options (Copper Mine Operating Flexibility, Abandonment Options, Backward Induction), Trading Operations & Speculation vs Hedging (Asset Management, Natural Resource Economics), Financial Policy & Liability Management (Naive vs Revised Equity Valuation, Debt Covenants, Commodity-Linked Bonds), Strategic Hedging & Long-term Exposure, Corporate Governance, Internal Control & Derivatives Debacles (Metallgesellschaft, Constellation Energy, Jefferson County).
   - Quy mô: 38 files (Course zip archive, 8 Lecture notes PDFs, 4 Problem sets, 4 Excel solution models, 5 HBS Case studies, 5 Book Chapters by Parsons & Mello, 2 Textbooks: Brealey-Myers-Allen & John Hull), 77.4 MB

12. **14.02 - Principles of Macroeconomics (Spring 2023)**
   - Đường dẫn: `/mnt/gdrive/Learning/MIT/14.02 - Principles of Macroeconomics (Spring 2023)`
   - Giảng viên: Prof. Ricardo Caballero (Department of Economics, MIT)
   - Nội dung: Macroeconomic Measurement (GDP, CPI, Unemployment), Goods Market & Multiplier, Financial Markets & Money Demand/Supply, IS-LM Model (Monetary & Fiscal Policy Mix), Extended IS-LM Model (Risk Premia, Shadow Banking, Liquidity Traps), Labor Markets (Wage-Setting & Price-Setting, Natural Rate of Unemployment), Phillips Curve (Adaptive vs Anchored Expectations), IS-LM-PC Dynamic Synthesis, Supply Shocks (Energy, Supply Chain, Stagflation), Theory of Economic Growth (Solow-Swan Model, Capital Accumulation, Golden Rule, Technological Progress, Balanced Growth Path, Convergence & Cross-Country Disparities), Open Economy Macroeconomics (Real Exchange Rate, Uncovered Interest Parity, Net Exports, Mundell-Fleming Model, Fixed vs Flexible Exchange Rates, Speculative Attacks, Euro Crisis), Expectations and Asset Pricing (Yield Curve, Term Structure of Interest Rates, Stock Valuation, Fundamental Value vs Bubbles, Forward-Looking IS-LM).
   - Quy mô: 80 files (Course archive zip, 25 Lecture notes & video transcripts PDF/WebVTT, 8 Problem sets & official full solutions, 3 Midterm Quizzes with solutions, Canonical Textbooks: Olivier Blanchard - Macroeconomics & In the Wake of the Crisis), 29.1 MB


---

## 🛠️ HƯỚNG DẪN CẬP NHẬT KHI TẢI KHÓA HỌC MỚI

Khi hoàn tất tải một khóa học mới, chạy lệnh kiểm tra dung lượng và số file:

```bash
# Xem số file và dung lượng thư mục vừa tải
python3 -c "
import os
path = '/mnt/gdrive/Learning/<Platform>/<Course-Folder>'
total_files = sum([len(files) for r, d, files in os.walk(path)])
total_size = sum([os.path.getsize(os.path.join(r, f)) for r, d, files in os.walk(path) for f in files])
print(f'Files: {total_files}, Size: {total_size / (1024*1024):.1f} MB ({total_size / (1024**3):.2f} GB)')
"
```

Sau đó:
1. Thêm 1 dòng vào **Bảng tra cứu nhanh**.
2. Thêm thông tin chi tiết vào phần **Chi tiết đường dẫn lưu trữ**.
3. Cập nhật ngày tháng tại dòng **Cập nhật lần cuối**.
