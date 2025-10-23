# backend/app.py - 最終完成版 (ロジック再構築・データ分析搭載)
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
import uuid
from datetime import datetime
import os
import numpy as np
from pdf_generator_final import generate_pdf_report_final

app = Flask(__name__)
CORS(app)

# --- ファイルパスの定義 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_PATH = os.path.join(BASE_DIR, '..', 'data', 'questions.json')
TYPE_LOGIC_PATH = os.path.join(BASE_DIR, '..', 'data', 'type_logic.json')
ANALYSIS_PATTERNS_PATH = os.path.join(BASE_DIR, '..', 'data', 'analysis_patterns.json')

# --- 設定ファイルの読み込み ---
try:
    with open(QUESTIONS_PATH, 'r', encoding='utf-8') as f:
        QUESTIONS_DATA = json.load(f)
    with open(TYPE_LOGIC_PATH, 'r', encoding='utf-8') as f:
        TYPE_LOGIC = json.load(f)
    with open(ANALYSIS_PATTERNS_PATH, 'r', encoding='utf-8') as f:
        ANALYSIS_PATTERNS = json.load(f)
except Exception as e:
    print(f"設定ファイルの読み込み中にエラーが発生しました: {e}"); exit()

# --- 診断ロジック ---
def calculate_creator_personality_advanced(answers, questions_data, logic_data):
    scores = {"Openness": 0, "Conscientiousness": 0, "Extraversion": 0, "Agreeableness": 0, "StressTolerance": 0, "InformationStyle": 0, "DecisionMaking": 0, "MotivationSource": 0, "ValuePursuit": 0, "WorkStyle": 0}
    for i, answer in enumerate(answers):
        question = questions_data['questions'][i]; dimension, score = question['dimension'], answer - 3
        scores[dimension] += score if question['direction'] == '+' else -score
    matched_cores = []
    for core_rule in logic_data['main_cores']:
        is_match = True
        if 'all' in core_rule['conditions']:
            for condition in core_rule['conditions']['all']:
                dim, op, val = condition['dimension'], condition['operator'], condition['value']
                if op == '>' and not scores[dim] > val: is_match = False; break
                if op == '<' and not scores[dim] < val: is_match = False; break
        if is_match: matched_cores.append(core_rule)
    if matched_cores:
        matched_cores.sort(key=lambda x: x['priority'], reverse=True)
        main_core = matched_cores[0]['type']
    else: main_core = logic_data['fallback_main_core']
    sub_core_scores = {sub_core: sum(scores[dim] * weight for dim, weight in details['scores'].items()) for sub_core, details in logic_data['sub_cores'].items()}
    sub_core = max(sub_core_scores, key=sub_core_scores.get)
    return main_core, sub_core, scores

# --- APIエンドポイント ---
@app.route('/api/questions', methods=['GET'])
def get_questions(): return jsonify(QUESTIONS_DATA)

@app.route('/api/start', methods=['POST'])
def start_test(): return jsonify({'user_id': str(uuid.uuid4()), 'started_at': datetime.now().isoformat()})

@app.route('/api/submit', methods=['POST'])
def submit_answers():
    data = request.json
    user_id, answers = data.get('user_id'), data.get('answers')
    if not all([user_id, answers, len(answers) == 20]): return jsonify({'error': '無効なデータ'}), 400
    main_core, sub_core, scores = calculate_creator_personality_advanced(answers, QUESTIONS_DATA, TYPE_LOGIC)
    analysis_data = ANALYSIS_PATTERNS.get(main_core, {}).get(sub_core, {})
    extreme_answers = sum(1 for ans in answers if ans == 1 or ans == 5)
    extremeness_score = (extreme_answers / 20) * 100
    if extremeness_score >= 75: extremeness_comment = "あなたは、自分の考えやスタイルが非常に明確で、白黒はっきりさせる傾向があります。この「尖った」姿勢が、熱狂的なファンを生む一方で、時には敵を作る可能性も秘めています。"
    elif extremeness_score >= 50: extremeness_comment = "あなたは、多くの事柄に対して自分の意見をしっかり持っているタイプです。その明確なスタンスが、あなたのクリエイターとしての個性や「色」に繋がっています。"
    else: extremeness_comment = "あなたは、物事を多角的に捉え、バランスの取れた判断をする傾向があります。その柔軟性は、多くの人に受け入れられやすい一方で、強い個性を出しにくい側面もあるかもしれません。"
    bf_scores = { "開放性": scores['Openness'], "誠実性": scores['Conscientiousness'], "外向性": scores['Extraversion'], "協調性": scores['Agreeableness'], "ストレス耐性": scores['StressTolerance'] }
    deviations = {k: abs(v) for k, v in bf_scores.items()}
    most_unique_trait = max(deviations, key=deviations.get)
    uniqueness_comment = f"あなたのビッグファイブ特性の中で、平均的な傾向から最も大きく離れているのは「{most_unique_trait}」です。これは、あなたのパーソナリティを特徴づける最もユニークな才能であり、他の人にはない強力な武器となる可能性を秘めています。"
    return jsonify({
        'user_id': user_id, 'main_core_name': ANALYSIS_PATTERNS.get(main_core, {}).get("name", main_core),
        'sub_core_title': analysis_data.get("sub_core_title", sub_core),
        'suited_for': analysis_data.get("suited_for"), 'not_suited_for': analysis_data.get("not_suited_for"),
        'synthesis': analysis_data.get("synthesis"),
        'radar_scores': {k: round(((v + 4) / 8) * 10, 1) for k, v in scores.items()},
        'data_analysis': { 'extremeness_score': round(extremeness_score), 'extremeness_comment': extremeness_comment, 'most_unique_trait': most_unique_trait, 'uniqueness_comment': uniqueness_comment },
        'completed_at': datetime.now().isoformat()
    })

@app.route('/api/generate_pdf', methods=['POST'])
def generate_pdf():
    result_data = request.json
    if not result_data: return jsonify({'error': 'PDF生成用のデータがありません'}), 400
    pdf_data = {
        'main_core_name': result_data.get('main_core_name'), 'sub_core_title': result_data.get('sub_core_title'),
        'suited_for': result_data.get('suited_for'), 'not_suited_for': result_data.get('not_suited_for'),
        'synthesis': result_data.get('synthesis'), 'radar_scores': result_data.get('radar_scores'),
    }
    pdf_buffer = generate_pdf_report_final("report", pdf_data)
    return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name='creator_core_report.pdf')

@app.route('/api/health', methods=['GET'])
def health_check(): return jsonify({'status': 'ok'})

if __name__ == '__main__': app.run(debug=True, port=5000)```
</details>

#### **5. `frontend/app/page.tsx` の差し替え**
<details>
<summary>クリックして `page.tsx` の全コードを表示</summary>

```tsx
// frontend/app/page.tsx - 最終完成版 (UI/UX改善対応)
'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import Image from 'next/image';
import { Radar } from 'react-chartjs-2';
import { Chart as ChartJS, RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend } from 'chart.js';

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:5000/api";

interface Question { q: string; }
interface QuestionsData { questions: Question[]; }
interface ResultData { user_id: string; main_core_name: string; sub_core_title: string; suited_for: string; not_suited_for: string; synthesis: string; radar_scores: { [key:string]: number }; data_analysis: { extremeness_score: number; extremeness_comment: string; most_unique_trait: string; uniqueness_comment: string; } }

const IconWrapper = ({ children }: { children: React.ReactNode }) => (<div className="flex items-center justify-center w-12 h-12 bg-red-100 dark:bg-gray-700 rounded-full mb-4">{children}</div>);

export default function Home() {
  const [started, setStarted] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<number[]>([]);
  const [userId, setUserId] = useState<string>('');
  const [questionsData, setQuestionsData] = useState<QuestionsData | null>(null);
  const [completed, setCompleted] = useState(false);
  const [result, setResult] = useState<ResultData | null>(null);
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => { axios.get(`${API_BASE}/questions`).then((res) => setQuestionsData(res.data)); }, []);
  const startTest = async () => { try { const res = await axios.post(`${API_BASE}/start`); setUserId(res.data.user_id); setStarted(true); } catch (e) { alert("診断を開始できませんでした。"); } };
  const handleAnswer = (value: number) => { if (isTransitioning) return; const newAnswers = [...answers, value]; setAnswers(newAnswers); setIsTransitioning(true); setTimeout(() => { if (currentQuestion < 19) { setCurrentQuestion(currentQuestion + 1); } else { submitAnswers(newAnswers); } setIsTransitioning(false); }, 200); };
  const goBack = () => { if (currentQuestion > 0 && !isTransitioning) { setIsTransitioning(true); setCurrentQuestion(currentQuestion - 1); setAnswers(answers.slice(0, -1)); setTimeout(() => setIsTransitioning(false), 200); } };
  const submitAnswers = async (finalAnswers: number[]) => { try { const res = await axios.post(`${API_BASE}/submit`, { user_id: userId, answers: finalAnswers, }); setResult(res.data); setCompleted(true); } catch (e) { alert("結果を送信できませんでした。"); } };
  const downloadPDF = async () => { if (!result) return; try { const response = await axios.post(`${API_BASE}/generate_pdf`, result, { responseType: 'blob' }); const url = window.URL.createObjectURL(new Blob([response.data])); const link = document.createElement('a'); link.href = url; link.setAttribute('download', 'creator_core_report.pdf'); document.body.appendChild(link); link.click(); link.parentNode?.removeChild(link); } catch (error) { alert("PDFのダウンロードに失敗しました。"); } };
  const restartTest = () => { setStarted(false); setCurrentQuestion(0); setAnswers([]); setUserId(''); setCompleted(false); setResult(null); };

  if (!started) { return ( <div className="min-h-screen bg-gray-50 text-gray-800 dark:bg-gray-900 dark:text-gray-100 transition-colors duration-300"> <main className="flex flex-col items-center justify-center min-h-screen p-6"> <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }} className="text-center"> <h1 className="text-4xl md:text-5xl font-bold mb-4 text-gray-900 dark:text-white">動画クリエイター特性診断</h1> <p className="text-lg md:text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto mb-12">20の質問から、あなたのクリエイターとしての「核」と、才能が輝くスタイルを発見します。</p> <motion.button onClick={startTest} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} className="bg-red-600 text-white font-bold py-4 px-12 rounded-full text-xl shadow-lg hover:bg-red-700 transition-colors">診断をはじめる</motion.button> </motion.div> <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.2 }} className="mt-20 max-w-4xl w-full grid md:grid-cols-2 gap-8"> <div className="bg-white dark:bg-gray-800 p-8 rounded-xl shadow-md"><IconWrapper><svg className="w-6 h-6 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg></IconWrapper><h3 className="text-xl font-bold mb-2">あなたの「本質」を理解する</h3><p className="text-gray-600 dark:text-gray-300">どのような環境で輝き、何を手放すべきか。あなたの生まれ持った特性を客観的に分析し、無理なく活動を続けるための指針を示します。</p></div> <div className="bg-white dark:bg-gray-800 p-8 rounded-xl shadow-md"><IconWrapper><svg className="w-6 h-6 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg></IconWrapper><h3 className="text-xl font-bold mb-2">最適な「創作スタイル」を発見する</h3><p className="text-gray-600 dark:text-gray-300">一人で黙々と作業するべきか、チームで協力するべきか。あなたの特性に合った動画の作り方や、チャンネル運営の方向性が明確になります。</p></div> </motion.div> </main> </div> ); }

  if (completed && result) {
    const radarLabels = ['開放性', '誠実性', '外向性', '協調性', 'ストレス耐性', '思考スタイル', '判断基準', 'モチベーション源泉', '創作スタンス', '作業環境'];
    const radarData = { labels: radarLabels, datasets: [{ label: 'あなたのスコア', data: result.radar_scores ? Object.values(result.radar_scores) : [], backgroundColor: 'rgba(239, 68, 68, 0.2)', borderColor: 'rgba(239, 68, 68, 1)', borderWidth: 2 }], };
    const radarOptions: any = { scales: { r: { beginAtZero: true, max: 10, ticks: { display: false }, grid: { color: 'rgba(0, 0, 0, 0.1)' }, pointLabels: { color: '#374151', font: { size: 14 } } } }, plugins: { legend: { display: false } } };
    return ( <div className="min-h-screen bg-gray-100 py-12"> <div className="container mx-auto px-4 sm:px-6 lg:px-8"> <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-4xl mx-auto bg-white rounded-2xl shadow-xl p-8 md:p-12">
      <div className="text-center mb-10">
        <div className="w-24 h-24 mx-auto mb-4 rounded-full overflow-hidden relative shadow-lg"><Image src="/hero.jpg" alt="Type Image" layout="fill" objectFit="cover" /></div>
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900">あなたは「{result.main_core_name || '診断中...'}」</h1>
        <h2 className="text-lg text-gray-500 font-normal mt-2">{result.sub_core_title || ''}</h2>
      </div>
      <div className="mb-12">
        <div className="max-w-xl mx-auto"><Radar data={radarData} options={radarOptions} /></div>
        <h2 className="text-2xl font-bold text-center text-gray-800 mt-6">あなたの特性分析</h2>
      </div>
      <div className="grid md:grid-cols-2 gap-8 mb-12">
        <div className="bg-green-50 border-l-4 border-green-500 p-6 rounded-r-lg"><h3 className="text-xl font-bold text-green-800 mb-3">向いていること</h3><p className="text-gray-700 leading-relaxed">{result.suited_for || '…'}</p></div>
        <div className="bg-orange-50 border-l-4 border-orange-500 p-6 rounded-r-lg"><h3 className="text-xl font-bold text-orange-800 mb-3">向いていないこと</h3><p className="text-gray-700 leading-relaxed">{result.not_suited_for || '…'}</p></div>
      </div>
      {result.data_analysis && (
      <div className="bg-purple-50 border-l-4 border-purple-500 p-8 rounded-r-lg mb-12">
        <h2 className="text-2xl font-bold text-purple-800 mb-4">あなたのユニークさ分析</h2>
        <div className="space-y-6">
          <div>
            <div className="flex justify-between items-center mb-1"><h3 className="font-bold text-gray-700">回答の明確さ（尖り度）</h3><span className="font-bold text-purple-700">{result.data_analysis.extremeness_score}%</span></div>
            <div className="w-full bg-gray-200 rounded-full h-2.5"><div className="bg-purple-500 h-2.5 rounded-full" style={{ width: `${result.data_analysis.extremeness_score}%` }}></div></div>
            <p className="text-sm text-gray-600 mt-2">{result.data_analysis.extremeness_comment}</p>
          </div>
          <div>
            <h3 className="font-bold text-gray-700">最も特徴的な才能</h3>
            <p className="text-sm text-gray-600 mt-2">{result.data_analysis.uniqueness_comment}</p>
          </div>
        </div>
      </div>
      )}
      <div className="bg-blue-50 p-8 rounded-2xl">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">分析結果まとめ</h2>
        <p className="text-gray-700 leading-loose whitespace-pre-line">{result.synthesis || '…'}</p>
      </div>
      <div className="flex flex-col sm:flex-row gap-4 justify-center mt-10">
        <button onClick={downloadPDF} className="bg-red-600 text-white font-bold py-3 px-8 rounded-full hover:bg-red-700">詳細レポートをダウンロード</button>
        <button onClick={restartTest} className="bg-gray-200 text-gray-800 font-bold py-3 px-8 rounded-full hover:bg-gray-300">もう一度診断する</button>
      </div>
    </motion.div> </div> </div> );
  }
  
  if (!questionsData) return <div className="flex justify-center items-center h-screen bg-gray-50">読み込み中...</div>;
  const progress = ((currentQuestion + 1) / 20) * 100;
  const currentQ = questionsData.questions[currentQuestion];
  return ( <div className="min-h-screen bg-gray-50 flex flex-col"> <div className="bg-white shadow-sm sticky top-0 z-10 p-4"> <div className="w-full bg-gray-200 rounded-full h-2.5"><motion.div className="bg-red-500 h-2.5 rounded-full" animate={{ width: `${progress}%` }} /></div> <p className="text-center text-sm text-gray-600 mt-2">{currentQuestion + 1} / 20</p> </div> <div className="flex-1 flex items-center justify-center p-4"> <AnimatePresence mode="wait"> <motion.div key={currentQuestion} initial={{ x: 300, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: -300, opacity: 0 }} transition={{ duration: 0.3 }} className="w-full max-w-2xl bg-white rounded-2xl shadow-lg p-8">
    <div className="flex items-center justify-center mb-6">
      <div className="flex items-center justify-center w-12 h-12 bg-red-500 text-white font-bold text-2xl rounded-full">Q</div>
      <div className="text-3xl font-bold text-gray-700 ml-3">{currentQuestion + 1}</div>
    </div>
    <h2 className="text-2xl font-bold text-gray-800 mb-8 text-center leading-relaxed">{currentQ.q}</h2>
    <div className="space-y-3"> {[{ v: 5, l: '非常にそう思う' }, { v: 4, l: 'ややそう思う' }, { v: 3, l: 'どちらとも言えない' }, { v: 2, l: 'あまりそう思わない' }, { v: 1, l: '全くそう思わない' }].map(o => (<button key={o.v} onClick={() => handleAnswer(o.v)} disabled={isTransitioning} className="w-full p-4 border rounded-lg hover:bg-red-50 hover:border-red-400 transition-colors text-left disabled:opacity-50"><span className="text-lg">{o.l}</span></button>))} </div>
  </motion.div> </AnimatePresence> </div> {currentQuestion > 0 && ( <button onClick={goBack} disabled={isTransitioning} className="fixed bottom-6 left-6 bg-white border-2 border-gray-300 text-gray-700 font-semibold py-2 px-5 rounded-full hover:border-red-500 hover:text-red-500 transition-all disabled:opacity-50 shadow-md"> ← 戻る </button> )} </div> );
}