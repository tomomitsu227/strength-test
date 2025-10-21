// app/page.tsx (改善版)
'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import './styles.css';

const API_BASE = 'http://localhost:5000/api';

interface Question {
  q: string;
  domain: string;
  category: string;
  weight: number;
}

interface QuestionsData {
  questions: Question[];
  domains: any;
}

export default function Home() {
  const [started, setStarted] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<number[]>([]);
  const [userId, setUserId] = useState<string>('');
  const [questionsData, setQuestionsData] = useState<QuestionsData | null>(null);
  const [completed, setCompleted] = useState(false);
  const [scores, setScores] = useState<any>(null);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [chartImages, setChartImages] = useState<any>(null);

  useEffect(() => {
    // 質問データの取得
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
    setScores(res.data.scores);
    
    // グラフ画像を取得
    try {
      const chartRes = await axios.get(`${API_BASE}/charts/${userId}`);
      setChartImages(chartRes.data);
    } catch (err) {
      console.error('グラフ取得エラー:', err);
    }
    
    setCompleted(true);
  };

  const downloadPDF = async () => {
    window.open(`${API_BASE}/pdf/${userId}`, '_blank');
  };

  const restartTest = () => {
    setStarted(false);
    setCurrentQuestion(0);
    setAnswers([]);
    setUserId('');
    setCompleted(false);
    setScores(null);
    setChartImages(null);
  };

  if (!questionsData) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>読み込み中...</p>
      </div>
    );
  }

  if (!started) {
    return (
      <div className="welcome-screen">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="welcome-content"
        >
          <div className="hero-section">
            <h1 className="main-title">あなたの強みを発見</h1>
            <p className="hero-subtitle">
              たった3分、20の質問で<br />
              あなたの隠れた才能と可能性を見つけましょう
            </p>
          </div>

          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">⏱️</div>
              <h3>たった3分</h3>
              <p>スキマ時間で完了</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🎯</div>
              <h3>高精度分析</h3>
              <p>科学的根拠に基づく診断</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <h3>詳細レポート</h3>
              <p>グラフで一目瞭然</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🔒</div>
              <h3>完全匿名</h3>
              <p>個人情報不要</p>
            </div>
          </div>

          <div className="how-it-works">
            <h2>診断の流れ</h2>
            <div className="steps">
              <div className="step">
                <div className="step-number">1</div>
                <div className="step-content">
                  <h4>20の質問に回答</h4>
                  <p>直感で答えてOK。正解はありません</p>
                </div>
              </div>
              <div className="step">
                <div className="step-number">2</div>
                <div className="step-content">
                  <h4>自動分析</h4>
                  <p>複数の心理学理論で多角的に分析</p>
                </div>
              </div>
              <div className="step">
                <div className="step-number">3</div>
                <div className="step-content">
                  <h4>結果を確認</h4>
                  <p>あなたの強みと特性をレポート表示</p>
                </div>
              </div>
            </div>
          </div>

          <div className="cta-section">
            <button className="start-button" onClick={startTest}>
              <span>今すぐ診断を始める</span>
              <span className="arrow">→</span>
            </button>
            <p className="cta-note">所要時間：約3分 | 会員登録不要</p>
          </div>
        </motion.div>
      </div>
    );
  }

  if (completed && scores) {
    return (
      <div className="result-screen">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="result-content"
        >
          <h1>あなたの診断結果</h1>
          <p className="result-intro">
            複数の心理学理論に基づき、あなたの特性を分析しました
          </p>

          {/* グラフ表示エリア */}
          {chartImages && (
            <div className="charts-section">
              <div className="chart-container">
                <h3>総合スコア</h3>
                <img src={chartImages.bar_chart} alt="総合スコアグラフ" />
              </div>
              <div className="chart-container">
                <h3>詳細分析</h3>
                <img src={chartImages.radar_chart} alt="レーダーチャート" />
              </div>
            </div>
          )}

          <div className="scores-summary">
            {Object.entries(scores.domain_scores).map(([key, value]: [string, any]) => (
              <div key={key} className="score-card">
                <h3>{value.name}</h3>
                <div className="score-value">{value.weighted_score.toFixed(1)}</div>
                <p className="score-description">{value.description}</p>
                <div className="score-bar">
                  <div
                    className="score-fill"
                    style={{ width: `${(value.weighted_score / 5) * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>

          <div className="result-actions">
            <button className="download-button" onClick={downloadPDF}>
              📥 詳細レポートをダウンロード
            </button>
            <button className="restart-button" onClick={restartTest}>
              🔄 もう一度診断する
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  const progress = ((currentQuestion + 1) / 20) * 100;
  const currentQ = questionsData.questions[currentQuestion];

  return (
    <div className="test-screen">
      <div className="progress-container">
        <div className="progress-bar">
          <motion.div
            className="progress-fill"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
        <p className="progress-text">
          {currentQuestion + 1} / 20
        </p>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={currentQuestion}
          initial={{ x: 300, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: -300, opacity: 0 }}
          transition={{ duration: 0.5, ease: 'easeInOut' }}
          className="question-card"
        >
          <h2 className="question-text">{currentQ.q}</h2>
          <div className="answer-options">
            {[1, 2, 3, 4, 5].map((value) => (
              <label key={value} className="radio-label">
                <input
                  type="radio"
                  name="answer"
                  value={value}
                  onChange={() => handleAnswer(value)}
                  disabled={isTransitioning}
                />
                <span className="radio-custom">
                  <span className="radio-number">{value}</span>
                </span>
                <span className="radio-text">
                  {value === 1 && '全くそう思わない'}
                  {value === 2 && 'あまりそう思わない'}
                  {value === 3 && 'どちらとも言えない'}
                  {value === 4 && 'ややそう思う'}
                  {value === 5 && '非常にそう思う'}
                </span>
              </label>
            ))}
          </div>
        </motion.div>
      </AnimatePresence>

      {currentQuestion > 0 && (
        <button className="back-button" onClick={goBack} disabled={isTransitioning}>
          ← 戻る
        </button>
      )}
    </div>
  );
}
