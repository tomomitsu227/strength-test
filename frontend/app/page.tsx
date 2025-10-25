import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { Radar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:5000/api';

interface Question {
  q: string;
}
interface QuestionsData {
  questions: Question[];
}
// suited_forとnot_suited_forをstring[]に変更
interface ResultData {
  user_id: string;
  main_core_name: string;
  sub_core_title: string;
  suited_for: string[];
  not_suited_for: string[];
  synthesis: string;
  radar_scores: { [key: string]: number };
}

const IconWrapper = ({ children }: { children: React.ReactNode }) => (
  <div className="flex items-center justify-center w-12 h-12 bg-red-100 dark:bg-gray-700 rounded-full mb-4">
    {children}
  </div>
);

export default function CreatorDiagnosisPage() {
  const [started, setStarted] = useState(false);
  const [questionsData, setQuestionsData] = useState<QuestionsData>();
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<number[]>([]);
  const [result, setResult] = useState<ResultData | null>(null);

  useEffect(() => {
    async function fetchQuestions() {
      const res = await axios.get(`${API_BASE}/questions`);
      setQuestionsData(res.data);
    }
    fetchQuestions();
  }, []);

  // handleAnswerをasyncに変更
  const handleAnswer = async (answer: number) => {
    const newAnswers = [...answers];
    newAnswers[currentQuestion] = answer;
    setAnswers(newAnswers);
    
    // 選択したことを視認させるために短い待機時間を設ける
    await new Promise(res => setTimeout(res, 250));

    if (currentQuestion < (questionsData?.questions.length || 0) - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      submitAnswers(newAnswers);
    }
  };

  const submitAnswers = async (ans: number[]) => {
    const user_id = 'user-' + Math.random().toString(36).slice(2, 8);
    try {
      const res = await axios.post(`${API_BASE}/submit`, {
        user_id,
        answers: ans
      });
      if (res.data && res.data.radar_scores) {
        setResult(res.data);
      } else {
        alert('診断結果の取得に失敗しました');
      }
    } catch (error) {
      console.error('診断結果取得エラー:', error);
      alert('診断結果取得時にエラーが発生しました');
    }
  };

  const handleDownloadPDF = async () => {
    if (!result) return;
    try {
      const response = await axios.get(
        `${API_BASE}/pdf/${result.user_id}`,
        { responseType: 'blob' }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `creator_core_report_${result.user_id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('PDF download error:', error);
      alert('PDFのダウンロードに失敗しました');
    }
  };

  if (!questionsData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-50 dark:from-gray-900 dark:to-gray-800">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">読み込み中...</p>
        </div>
      </div>
    );
  }

  // トップページ（診断開始前）
  if (!started && !result) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 via-orange-50 to-yellow-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
        <div className="container mx-auto px-4 py-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center mb-12"
          >
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 dark:text-white mb-6">
              動画クリエイター特性診断
            </h1>
            <p className="text-xl md:text-2xl text-gray-700 dark:text-gray-300 mb-8">
              20の質問から、あなたのクリエイターとしての「核」と、才能が輝くスタイルを発見します。
            </p>
          </motion.div>
          <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto mb-12">
            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6, delay: 0.2 }} className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl">
              <IconWrapper>
                <svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
              </IconWrapper>
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">あなたの「本質」を理解する</h3>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">どのような環境で輝き、何を手放すべきか。あなたの生まれ持った特性を客観的に分析し、無理なく活動を続けるための指針を示します。</p>
            </motion.div>
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6, delay: 0.4 }} className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl">
              <IconWrapper>
                <svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
              </IconWrapper>
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">最適な「創作スタイル」を発見する</h3>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">一人で黙々と作業するべきか、チームで協力するべきか。あなたの特性に合った動画の作り方や、チャンネル運営の方向性が明確になります。</p>
            </motion.div>
          </div>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.6 }} className="text-center">
            <button onClick={() => setStarted(true)} className="bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white text-xl font-bold py-6 px-12 rounded-full shadow-2xl transform hover:scale-105 transition-all duration-300">
              診断を始める
            </button>
            <p className="mt-6 text-gray-500 dark:text-gray-400">所要時間: 約3分</p>
          </motion.div>
        </div>
      </div>
    );
  }

  // 質問画面
  if (!result && started) {
    const q = questionsData.questions[currentQuestion];
    const progress = ((currentQuestion + 1) / questionsData.questions.length) * 100;

    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center px-4">
        <div className="max-w-3xl w-full">
          <div className="mb-8">
            <div className="flex justify-end items-center mb-2">
              <span className="text-sm font-semibold text-red-500">{Math.round(progress)}%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <motion.div
                initial={{ width: `${(progress - 5)}%`}}
                animate={{ width: `${progress}%` }}
                className="bg-gradient-to-r from-red-500 to-orange-500 h-2 rounded-full"
                transition={{ duration: 0.3 }}
              />
            </div>
          </div>
          <AnimatePresence mode="wait">
            <motion.div
              key={currentQuestion}
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -50 }}
              transition={{ duration: 0.3 }}
              className="bg-white dark:bg-gray-800 rounded-2xl p-8 md:p-12 shadow-2xl"
            >
              <div className="flex items-center gap-4 mb-8">
                <div className="flex items-center justify-center w-12 h-12 bg-red-500 text-white font-bold text-2xl rounded-full">Q</div>
                <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white leading-relaxed">
                  {q.q}
                </h2>
              </div>
              <div className="space-y-4">
                {[
                  { value: 5, label: 'とても当てはまる' },
                  { value: 4, label: 'やや当てはまる' },
                  { value: 3, label: 'どちらとも言えない' },
                  { value: 2, label: 'あまり当てはまらない' },
                  { value: 1, label: '全く当てはまらない' }
                ].map((option) => (
                  <button key={option.value} onClick={() => handleAnswer(option.value)} className={`w-full text-left p-4 rounded-xl border-2 transition-all duration-200 ${ answers[currentQuestion] === option.value ? 'border-red-500 bg-red-50 dark:bg-red-900/20' : 'border-gray-200 dark:border-gray-700 hover:border-red-300 dark:hover:border-red-700'}`}>
                    <div className="flex items-center">
                      <div className={`w-6 h-6 rounded-full border-2 mr-4 flex items-center justify-center ${ answers[currentQuestion] === option.value ? 'border-red-500 bg-red-500' : 'border-gray-300 dark:border-gray-600'}`}>
                        {answers[currentQuestion] === option.value && (<svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>)}
                      </div>
                      <span className="text-gray-700 dark:text-gray-300 font-medium">{option.label}</span>
                    </div>
                  </button>
                ))}
              </div>
              {currentQuestion > 0 && (
                <button onClick={() => setCurrentQuestion(currentQuestion - 1)} className="mt-6 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 flex items-center">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
                  前の質問に戻る
                </button>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    );
  }

  // 結果表示画面
  if (result) {
    const radarLabels = ['独創性','計画性','社交性','共感力','精神的安定性','創作スタイル','協働適性'];
    const radarData = {
      labels: radarLabels,
      datasets: [{
          label: 'あなたのスコア',
          data: radarLabels.map(label => result.radar_scores?.[label] || 0),
          backgroundColor: 'rgba(239,68,68,0.2)',
          borderColor: '#EF4444',
          pointBackgroundColor: '#EF4444',
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: '#EF4444'
      }]
    };
    const radarOptions = {
      scales: { r: { min: 2, max: 10, ticks: { stepSize: 2, color: '#6B7280', font: { size: 12 }}, pointLabels: { font: { size: 14, family: 'Noto Sans JP, sans-serif' }, color: '#374151' }, grid: { color: '#E5E7EB' }}},
      plugins: { legend: { display: false }}
    };

    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 dark:from-gray-900 dark:to-gray-800 py-12 px-4">
        <div className="max-w-4xl mx-auto">
          <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4">診断結果</h1>
            <p className="text-gray-600 dark:text-gray-400">あなたのクリエイタータイプが判明しました</p>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl mb-8">
            <div className="text-center">
              <p className="text-lg text-gray-600 dark:text-gray-400 mb-4">あなたは</p>
              <h2 className="text-3xl md:text-4xl font-bold text-red-500">『{result.main_core_name}』</h2>
              <p className="text-xl text-gray-700 dark:text-gray-300 mt-3">～{result.sub_core_title}～</p>
            </div>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl mb-8">
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 text-center">あなたの特性プロファイル</h3>
            <div className="max-w-2xl mx-auto">
              <Radar data={radarData} options={radarOptions} />
            </div>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="grid md:grid-cols-2 gap-6 mb-8">
            <div className="bg-green-50 dark:bg-green-900/20 border-l-4 border-green-500 rounded-r-2xl p-6 shadow-lg">
              <h3 className="text-xl font-bold text-green-700 dark:text-green-400 mb-4 flex items-center">
                <svg className="w-6 h-6 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
                向いていること
              </h3>
              <ul className="space-y-2 list-disc list-inside text-gray-700 dark:text-gray-300">
                {result.suited_for.map((item, index) => <li key={index}>{item}</li>)}
              </ul>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700/20 border-l-4 border-gray-500 rounded-r-2xl p-6 shadow-lg">
              <h3 className="text-xl font-bold text-gray-700 dark:text-gray-400 mb-4 flex items-center">
                <svg className="w-6 h-6 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
                向いていないこと
              </h3>
               <ul className="space-y-2 list-disc list-inside text-gray-700 dark:text-gray-300">
                {result.not_suited_for.map((item, index) => <li key={index}>{item}</li>)}
              </ul>
            </div>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }} className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl mb-8">
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">分析結果のまとめ</h3>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">{result.synthesis || '…'}</p>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 }} className="flex flex-col sm:flex-row gap-4 justify-center">
            <button onClick={handleDownloadPDF} className="bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white font-bold py-4 px-8 rounded-full shadow-lg transform hover:scale-105 transition-all duration-300">
              <svg className="w-5 h-5 inline-block mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              PDFでダウンロード
            </button>
            <button onClick={() => { setStarted(false); setResult(null); setAnswers([]); setCurrentQuestion(0);}} className="bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 font-bold py-4 px-8 rounded-full shadow-lg transform hover:scale-105 transition-all duration-300">
              もう一度診断する
            </button>
          </motion.div>
        </div>
      </div>
    );
  }

  return null;
}