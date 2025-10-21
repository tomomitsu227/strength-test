// app/page.tsx - TailwindベースYouTube強み診断
'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import Image from 'next/image';

const API_BASE = 'http://localhost:5000/api';

interface Question {
  q: string;
  type: string;
  weight: number;
}

interface QuestionsData {
  questions: Question[];
}

export default function Home() {
  const [started, setStarted] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<number[]>([]);
  const [userId, setUserId] = useState<string>('');
  const [questionsData, setQuestionsData] = useState<QuestionsData | null>(null);
  const [completed, setCompleted] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    axios.get(`${API_BASE}/questions`).then((res) => {
      setQuestionsData(res.data);
    });
  }, []);

  const startTest = async () => {
    const res = await axios.post(`${API_BASE}/start`);
    setUserId(res.data.user_id);
    setStarted(true);
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
    }, 500);
  };

  const goBack = () => {
    if (currentQuestion > 0 && !isTransitioning) {
      setCurrentQuestion(currentQuestion - 1);
      setAnswers(answers.slice(0, -1));
    }
  };

  const submitAnswers = async (finalAnswers: number[]) => {
    const res = await axios.post(`${API_BASE}/submit`, {
      user_id: userId,
      answers: finalAnswers,
    });
    setResult(res.data);
    setCompleted(true);
  };

  const downloadPDF = () => {
    window.open(`${API_BASE}/pdf/${userId}`, '_blank');
  };

  const restartTest = () => {
    setStarted(false);
    setCurrentQuestion(0);
    setAnswers([]);
    setUserId('');
    setCompleted(false);
    setResult(null);
  };

  if (!questionsData) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
        <p className="mt-4 text-gray-600">読み込み中...</p>
      </div>
    );
  }

  if (!started) {
    return (
      <div className="bg-gray-50 text-gray-800">
        {/* ヘッダー */}
        <header className="bg-white/80 backdrop-blur-md sticky top-0 z-50 border-b border-gray-200">
          <div className="container mx-auto px-6 py-4 flex justify-between items-center">
            <div className="font-bold text-xl text-gray-900 flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              強み発見ナビ
            </div>
            <nav className="hidden md:flex items-center space-x-8">
              <a href="#features" className="text-gray-600 hover:text-red-500 transition-colors">診断でわかること</a>
              <a href="#how-to" className="text-gray-600 hover:text-red-500 transition-colors">ご利用の流れ</a>
            </nav>
            <button onClick={startTest} className="bg-red-500 text-white font-bold py-2 px-6 rounded-full hover:bg-red-600 transition-transform transform hover:scale-105 shadow-md">
              無料診断スタート
            </button>
          </div>
        </header>

        <main>
          {/* ヒーローセクション */}
          <section className="py-20 md:py-32 bg-white">
            <div className="container mx-auto px-6">
              <div className="grid md:grid-cols-2 gap-12 items-center">
                <motion.div
                  initial={{ opacity: 0, x: -30 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.8 }}
                >
                  <span className="text-red-500 font-semibold uppercase tracking-wider">YouTubeで成功する、最初のステップ</span>
                  <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mt-4 mb-6 leading-tight">
                    あなたの「強み」を<br />「稼げる動画」に変える
                  </h1>
                  <p className="text-lg md:text-xl text-gray-600 mb-10">
                    簡単な5分間の診断で、あなたに最適なYouTubeジャンルと成功戦略がわかる。もう、何を発信すればいいか迷わない。
                  </p>
                  <button onClick={startTest} className="bg-red-500 text-white font-bold py-4 px-10 rounded-full hover:bg-red-600 transition-transform transform hover:scale-105 text-lg shadow-lg">
                    今すぐ無料であなたの強みを診断
                  </button>
                  <p className="mt-4 text-sm text-gray-500">登録不要・完全無料</p>
                </motion.div>
                <motion.div
                  initial={{ opacity: 0, x: 30 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.8, delay: 0.2 }}
                  className="relative"
                >
                  <Image
                    src="/hero.jpg"
                    alt="Discovery through Diagnosis"
                    width={600}
                    height={600}
                    className="w-full h-auto"
                    priority
                  />
                </motion.div>
              </div>
            </div>
          </section>

          {/* 問題提起セクション */}
          <section className="py-16 md:py-24 bg-gradient-to-br from-gray-50 to-gray-100">
            <div className="container mx-auto px-6">
              <div className="text-center mb-12">
                <h2 className="text-3xl md:text-4xl font-bold text-gray-900">こんなお悩み、ありませんか？</h2>
                <p className="mt-4 text-gray-600">一つでも当てはまったら、この診断がきっと役立ちます。</p>
              </div>
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
                {[
                  { icon: '❓', title: '何から始めるべきか', desc: '発信したいことはあるけど、何から手をつければいいか分からない。' },
                  { icon: '🎯', title: '自分の強みが不明', desc: '自分にどんな才能があるのか、どんなジャンルが向いているのか確信が持てない。' },
                  { icon: '📊', title: '他の人との差別化', desc: '多くのライバルの中で、どうすれば自分のチャンネルが埋もれないか不安。' },
                  { icon: '📈', title: '収益化への道のり', desc: '動画作りを楽しみたいけど、ビジネスとして成立させられるか心配。' }
                ].map((item, i) => (
                  <div key={i} className="bg-white p-8 rounded-2xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                    <div className="text-4xl mb-4">{item.icon}</div>
                    <h3 className="font-bold text-xl mb-2">{item.title}</h3>
                    <p className="text-gray-600">{item.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* メリットセクション */}
          <section id="features" className="py-16 md:py-24 bg-white">
            <div className="container mx-auto px-6">
              <div className="text-center mb-12">
                <h2 className="text-3xl md:text-4xl font-bold text-gray-900">この診断でわかること</h2>
                <p className="mt-4 text-gray-600 max-w-2xl mx-auto">あなたのYouTubeチャンネル成功の鍵となる、3つの要素を明らかにします。</p>
              </div>
              <div className="grid md:grid-cols-3 gap-8">
                {[
                  { num: '01', title: 'あなたの才能トップ3', desc: '独自のアルゴリズムで、あなたの性格や興味から「動画に活かせる強み」を分析します。' },
                  { num: '02', title: '最適なチャンネルジャンル', desc: '強みを最大限に活かせる、具体的なYouTubeジャンルを複数提案。あなただけのブルーオーシャンが見つかります。' },
                  { num: '03', title: '成功へのロードマップ', desc: '提案ジャンルで成功するための、コンテンツの方向性や参考チャンネルなど、具体的なアクションプランを提示します。' }
                ].map((item, i) => (
                  <div key={i} className={`bg-gradient-to-br ${i === 1 ? 'from-red-50 to-red-100 scale-105' : 'from-gray-50 to-gray-100'} p-8 rounded-2xl shadow-lg text-center`}>
                    <div className="text-3xl font-bold text-red-500 mb-4">{item.num}</div>
                    <h3 className="font-bold text-2xl mb-2">{item.title}</h3>
                    <p className="text-gray-600">{item.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* ご利用の流れ */}
          <section id="how-to" className="py-16 md:py-24 bg-gradient-to-br from-gray-50 to-gray-100">
            <div className="container mx-auto px-6">
              <div className="text-center mb-12">
                <h2 className="text-3xl md:text-4xl font-bold text-gray-900">診断はかんたん3ステップ</h2>
                <p className="mt-4 text-gray-600">約5分で、あなたの可能性が広がります。</p>
              </div>
              <div className="grid md:grid-cols-3 gap-12 relative">
                {[
                  { num: '1', title: '質問に答える', desc: '直感でサクサク答えられる20の質問に回答します。' },
                  { num: '2', title: '結果を分析', desc: '独自のロジックであなたの強みや適性を瞬時に分析します。' },
                  { num: '3', title: 'レポート確認', desc: 'あなただけの強みと、YouTube戦略レポートが完成します。' }
                ].map((item, i) => (
                  <div key={i} className="text-center">
                    <div className="w-24 h-24 mx-auto bg-red-100 border-2 border-red-500 text-red-500 rounded-full flex items-center justify-center font-bold text-3xl mb-4">{item.num}</div>
                    <h3 className="font-bold text-xl mb-2">{item.title}</h3>
                    <p className="text-gray-600">{item.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* CTA */}
          <section className="py-16 md:py-24 bg-white">
            <div className="container mx-auto px-6 text-center">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">さあ、あなたの才能を見つけよう</h2>
              <p className="text-lg text-gray-700 max-w-2xl mx-auto mb-10">
                YouTubeは、あなたの個性が輝く場所。その第一歩を、この診断から始めませんか？
              </p>
              <button onClick={startTest} className="bg-red-500 text-white font-bold py-4 px-10 rounded-full hover:bg-red-600 transition-transform transform hover:scale-105 text-lg shadow-lg">
                無料で診断を始める
              </button>
              <p className="mt-4 text-sm text-gray-600">診断結果はすぐに確認できます</p>
            </div>
          </section>
        </main>

        {/* フッター */}
        <footer className="bg-gray-900 text-white py-8">
          <div className="container mx-auto px-6 text-center">
            <p>&copy; 2025 強み発見ナビ. All Rights Reserved.</p>
            <div className="mt-4 space-x-6 text-sm">
              <a href="#" className="text-gray-400 hover:text-white">利用規約</a>
              <a href="#" className="text-gray-400 hover:text-white">プライバシーポリシー</a>
            </div>
          </div>
        </footer>
      </div>
    );
  }

  if (completed && result) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-12">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-4xl mx-auto"
          >
            <div className="bg-white rounded-3xl shadow-2xl p-8 md:p-12">
              <div className="text-center mb-8">
                <div className="text-6xl mb-4">{result.animal_icon}</div>
                <h1 className="text-4xl font-bold text-gray-900 mb-2">あなたは「{result.animal_name}」タイプ</h1>
                <p className="text-xl text-gray-600">{result.animal_description}</p>
              </div>

              <div className="grid md:grid-cols-3 gap-6 mb-8">
                {result.top_strengths.map((strength: string, i: number) => (
                  <div key={i} className="bg-gradient-to-br from-red-50 to-red-100 p-6 rounded-xl text-center">
                    <div className="text-2xl font-bold text-red-500 mb-2">強み {i + 1}</div>
                    <p className="font-semibold text-gray-900">{strength}</p>
                  </div>
                ))}
              </div>

              <div className="bg-gray-50 p-8 rounded-2xl mb-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-4">🎯 あなたに最適なYouTube戦略</h3>
                <div className="space-y-4 text-gray-700">
                  <p><strong>おすすめジャンル:</strong> {result.youtube_strategy.genre}</p>
                  <p><strong>コンテンツの方向性:</strong> {result.youtube_strategy.direction}</p>
                  <p><strong>成功のポイント:</strong> {result.youtube_strategy.success_tips}</p>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <button onClick={downloadPDF} className="bg-red-500 text-white font-bold py-3 px-8 rounded-full hover:bg-red-600 transition-transform transform hover:scale-105 shadow-lg">
                  📥 詳細レポートをダウンロード
                </button>
                <button onClick={restartTest} className="bg-white border-2 border-red-500 text-red-500 font-bold py-3 px-8 rounded-full hover:bg-red-50 transition-transform transform hover:scale-105">
                  🔄 もう一度診断する
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

  const progress = ((currentQuestion + 1) / 20) * 100;
  const currentQ = questionsData.questions[currentQuestion];

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <div className="bg-white shadow-md sticky top-0 z-10">
        <div className="container mx-auto px-6 py-4">
          <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
            <motion.div
              className="bg-gradient-to-r from-red-400 to-red-600 h-3 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
          <p className="text-center text-sm text-gray-600">{currentQuestion + 1} / 20</p>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentQuestion}
            initial={{ x: 300, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -300, opacity: 0 }}
            transition={{ duration: 0.5, ease: 'easeInOut' }}
            className="w-full max-w-3xl bg-white rounded-3xl shadow-2xl p-8 md:p-12"
          >
            <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-8 leading-relaxed">{currentQ.q}</h2>
            <div className="space-y-4">
              {[
                { value: 5, label: '非常にそう思う' },
                { value: 4, label: 'ややそう思う' },
                { value: 3, label: 'どちらとも言えない' },
                { value: 2, label: 'あまりそう思わない' },
                { value: 1, label: '全くそう思わない' }
              ].map((option) => (
                <button
                  key={option.value}
                  onClick={() => handleAnswer(option.value)}
                  disabled={isTransitioning}
                  className="w-full flex items-center p-4 border-2 border-gray-200 rounded-xl hover:border-red-500 hover:bg-red-50 transition-all disabled:opacity-50"
                >
                  <div className="w-10 h-10 flex items-center justify-center rounded-full border-2 border-gray-300 text-gray-600 font-semibold mr-4">
                    {option.value}
                  </div>
                  <span className="text-lg text-gray-700">{option.label}</span>
                </button>
              ))}
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {currentQuestion > 0 && (
        <button
          onClick={goBack}
          disabled={isTransitioning}
          className="fixed bottom-8 left-8 bg-white border-2 border-gray-300 text-gray-700 font-semibold py-3 px-6 rounded-full hover:border-red-500 hover:text-red-500 transition-all disabled:opacity-50 shadow-lg"
        >
          ← 戻る
        </button>
      )}
    </div>
  );
}
