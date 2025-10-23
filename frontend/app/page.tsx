// frontend/app/page.tsx - 新デザイン対応版
'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { Radar } from 'react-chartjs-2';
import {
  Chart as ChartJS, RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend,
} from 'chart.js';

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:5000/api";

interface Question { q: string; }
interface QuestionsData { questions: Question[]; }
// ★★★ 変更点：APIからの結果の型定義を更新 ★★★
interface ResultData {
  type_name: string;
  icon: string;
  description: string;
  focus_on: string;
  let_go_of: string;
  synthesis: string;
  radar_scores: { [key: string]: number };
}

export default function Home() {
  const [started, setStarted] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<number[]>([]);
  const [userId, setUserId] = useState<string>('');
  const [questionsData, setQuestionsData] = useState<QuestionsData | null>(null);
  const [completed, setCompleted] = useState(false);
  const [result, setResult] = useState<ResultData | null>(null);
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    axios.get(`${API_BASE}/questions`).then((res) => setQuestionsData(res.data));
  }, []);

  const startTest = async () => {
    try {
      const res = await axios.post(`${API_BASE}/start`);
      setUserId(res.data.user_id);
      setStarted(true);
    } catch (error) {
      console.error("Failed to start test:", error);
      alert("診断を開始できませんでした。サーバーが起動しているか確認してください。");
    }
  };

  const handleAnswer = async (value: number) => {
    if (isTransitioning) return;
    const newAnswers = [...answers, value];
    setAnswers(newAnswers);
    setIsTransitioning(true);
    setTimeout(() => {
      if (currentQuestion < 19) {
        setCurrentQuestion(currentQuestion + 1);
      } else {
        submitAnswers(newAnswers);
      }
      setIsTransitioning(false);
    }, 200);
  };

  const submitAnswers = async (finalAnswers: number[]) => {
    try {
      const res = await axios.post(`${API_BASE}/submit`, {
        user_id: userId,
        answers: finalAnswers,
      });
      setResult(res.data);
      setCompleted(true);
    } catch (error) {
      console.error("Failed to submit answers:", error);
      alert("結果を送信できませんでした。もう一度お試しください。");
    }
  };

  const restartTest = () => {
    setStarted(false); setCurrentQuestion(0); setAnswers([]); setUserId(''); setCompleted(false); setResult(null);
  };

  // --- トップページ（ランディングページ） ---
  if (!started) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-900 text-white p-6">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center"
        >
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            動画クリエイター・コアファインダー
          </h1>
          <p className="text-lg md:text-xl text-gray-300 max-w-2xl mx-auto mb-10">
            20の質問に答えるだけで、あなたのクリエイターとしての「核」となる本質と、才能が最も輝くスタイルを発見します。
          </p>
          <motion.button
            onClick={startTest}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="bg-red-600 text-white font-bold py-4 px-12 rounded-full text-xl shadow-lg hover:bg-red-700 transition-colors"
          >
            診断をはじめる
          </motion.button>
        </motion.div>
      </div>
    );
  }

  // --- 診断結果ページ ---
  if (completed && result) {
    const radarData = {
      labels: ['開放性', '誠実性', '外向性', '協調性', 'ストレス耐性', '情報スタイル', '意思決定', 'モチベーション', '価値追求', '作業スタイル'],
      datasets: [{
        label: 'あなたのスコア',
        data: Object.values(result.radar_scores),
        backgroundColor: 'rgba(239, 68, 68, 0.2)',
        borderColor: 'rgba(239, 68, 68, 1)',
        borderWidth: 2,
      }],
    };
    const radarOptions = { scales: { r: { beginAtZero: true, max: 10, ticks: { display: false }, pointLabels: { font: { size: 14 } } } }, plugins: { legend: { display: false } } };

    return (
      <div className="min-h-screen bg-gray-100 py-12">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-4xl mx-auto bg-white rounded-2xl shadow-xl p-8 md:p-12">
            
            <div className="text-center mb-10">
              <div className="text-6xl mb-4">{result.icon}</div>
              <h1 className="text-3xl md:text-4xl font-bold text-gray-900">あなたは「{result.type_name}」タイプ</h1>
              <p className="text-lg text-gray-600 mt-2">{result.description}</p>
            </div>
            
            <div className="grid md:grid-cols-2 gap-8 mb-10">
              <div className="bg-green-50 border-l-4 border-green-500 p-6 rounded-r-lg">
                <h3 className="text-xl font-bold text-green-800 mb-3">注力すること</h3>
                <p className="text-gray-700 leading-relaxed">{result.focus_on}</p>
              </div>
              <div className="bg-orange-50 border-l-4 border-orange-500 p-6 rounded-r-lg">
                <h3 className="text-xl font-bold text-orange-800 mb-3">手放すこと</h3>
                <p className="text-gray-700 leading-relaxed">{result.let_go_of}</p>
              </div>
            </div>

            <div className="mb-10">
              <h2 className="text-2xl font-bold text-center text-gray-800 mb-4">あなたの特性分析</h2>
              <div className="max-w-md mx-auto">
                <Radar data={radarData} options={radarOptions} />
              </div>
            </div>

            <div className="bg-blue-50 p-8 rounded-2xl">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">診断結果の統括 - あなたの本質</h2>
              <p className="text-gray-700 leading-loose whitespace-pre-line">{result.synthesis}</p>
            </div>

            <div className="text-center mt-10">
              <button onClick={restartTest} className="bg-gray-200 text-gray-800 font-bold py-3 px-8 rounded-full hover:bg-gray-300 transition-colors">
                もう一度診断する
              </button>
            </div>

          </motion.div>
        </div>
      </div>
    );
  }
  
  // --- 質問ページ (変更なし) ---
  if (!questionsData) return <div className="flex justify-center items-center h-screen">読み込み中...</div>;
  const progress = ((currentQuestion + 1) / 20) * 100;
  const currentQ = questionsData.questions[currentQuestion];
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <div className="bg-white shadow-sm sticky top-0 z-10 p-4">
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <motion.div className="bg-red-500 h-2.5 rounded-full" animate={{ width: `${progress}%` }} />
        </div>
        <p className="text-center text-sm text-gray-600 mt-2">{currentQuestion + 1} / 20</p>
      </div>
      <div className="flex-1 flex items-center justify-center p-4">
        <AnimatePresence mode="wait">
          <motion.div key={currentQuestion} initial={{ x: 300, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: -300, opacity: 0 }} transition={{ duration: 0.3 }} className="w-full max-w-2xl bg-white rounded-2xl shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-8 text-center leading-relaxed">{currentQ.q}</h2>
            <div className="space-y-3">
              {[{ v: 5, l: '非常にそう思う' }, { v: 4, l: 'ややそう思う' }, { v: 3, l: 'どちらとも言えない' }, { v: 2, l: 'あまりそう思わない' }, { v: 1, l: '全くそう思わない' }].map(o => (
                <button key={o.v} onClick={() => handleAnswer(o.v)} disabled={isTransitioning} className="w-full p-4 border rounded-lg hover:bg-red-50 hover:border-red-400 transition-colors text-left disabled:opacity-50">
                  <span className="text-lg">{o.l}</span>
                </button>
              ))}
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}