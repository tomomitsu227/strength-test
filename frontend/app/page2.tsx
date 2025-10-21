// app/page.tsx
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

    // 自動で次の質問へ遷移
    setTimeout(() => {
      if (currentQuestion < 19) {
        setCurrentQuestion(currentQuestion + 1);
      } else {
        // 全て回答完了
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
    setCompleted(true);
  };

  const downloadPDF = async () => {
    window.open(`${API_BASE}/pdf/${userId}`, '_blank');
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
          <h1>あなたの強みを診断</h1>
          <p className="subtitle">20の質問であなたの特性を分析します</p>
          <div className="domains-overview">
            <div className="domain-card">
              <h3>4脳分類</h3>
              <p>思考スタイルの傾向</p>
            </div>
            <div className="domain-card">
              <h3>VIA強み</h3>
              <p>ポジティブ心理学ベース</p>
            </div>
            <div className="domain-card">
              <h3>ストレングスファインダー</h3>
              <p>ビジネス実用性重視</p>
            </div>
            <div className="domain-card">
              <h3>モチベーション維持</h3>
              <p>継続的成長の要素</p>
            </div>
          </div>
          <button className="start-button" onClick={startTest}>
            診断を開始する
          </button>
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
          <h1>診断結果</h1>
          <div className="scores-summary">
            {Object.entries(scores.domain_scores).map(([key, value]: [string, any]) => (
              <div key={key} className="score-card">
                <h3>{value.name}</h3>
                <div className="score-value">{value.weighted_score.toFixed(2)}</div>
                <p className="score-description">{value.description}</p>
                <div className="evidence-bar">
                  <div
                    className="evidence-fill"
                    style={{ width: `${value.evidence_weight * 100}%` }}
                  ></div>
                </div>
                <p className="evidence-label">
                  エビデンス強度: {(value.evidence_weight * 100).toFixed(0)}%
                </p>
              </div>
            ))}
          </div>
          <button className="download-button" onClick={downloadPDF}>
            詳細レポートをダウンロード (PDF)
          </button>
        </motion.div>
      </div>
    );
  }

  const progress = ((currentQuestion + 1) / 20) * 100;
  const currentQ = questionsData.questions[currentQuestion];

  return (
    <div className="test-screen">
      {/* 進捗バー */}
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

      {/* 質問カード */}
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

      {/* 戻るボタン */}
      {currentQuestion > 0 && (
        <button className="back-button" onClick={goBack} disabled={isTransitioning}>
          ← 戻る
        </button>
      )}
    </div>
  );
}
