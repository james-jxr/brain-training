import React from 'react';
import Sidebar from '../components/nav/Sidebar';
import Card from '../components/ui/Card';

const AboutScience = () => {
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <main style={{
        flex: 1,
        padding: 'var(--space-6)',
        overflowY: 'auto',
      }}>
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
          <h1 style={{ marginBottom: 'var(--space-8)' }}>The Science Behind Brain Training</h1>

          <Card style={{ marginBottom: 'var(--space-6)' }}>
            <h2>Cognitive Domains</h2>
            <p style={{ marginBottom: 'var(--space-4)' }}>
              Brain Training targets three fundamental cognitive abilities that underpin overall mental performance:
            </p>

            <h3 style={{ marginTop: 'var(--space-6)', marginBottom: 'var(--space-2)' }}>Processing Speed</h3>
            <p style={{ marginBottom: 'var(--space-4)', color: 'var(--color-text-secondary)' }}>
              The ability to quickly perceive, process, and respond to information. This is fundamental to all cognitive tasks and influences how efficiently you can complete complex mental activities.
            </p>

            <h3 style={{ marginTop: 'var(--space-6)', marginBottom: 'var(--space-2)' }}>Working Memory</h3>
            <p style={{ marginBottom: 'var(--space-4)', color: 'var(--color-text-secondary)' }}>
              Your ability to temporarily hold and manipulate information in your mind. Strong working memory is essential for reasoning, problem-solving, and learning.
            </p>

            <h3 style={{ marginTop: 'var(--space-6)', marginBottom: 'var(--space-2)' }}>Attention</h3>
            <p style={{ color: 'var(--color-text-secondary)' }}>
              The capacity to focus and maintain concentration. Attention controls which information your brain processes and directly affects the quality of your cognitive performance.
            </p>
          </Card>

          <Card style={{ marginBottom: 'var(--space-6)' }}>
            <h2>Adaptive Difficulty</h2>
            <p style={{ marginBottom: 'var(--space-4)' }}>
              Our system uses evidence-based adaptive algorithms to optimize your learning. Research shows that the "sweet spot" for learning is when you succeed at 70-80% of tasks. We automatically adjust difficulty to keep you in this zone.
            </p>
            <p style={{ color: 'var(--color-text-secondary)' }}>
              This prevents both boredom (from tasks that are too easy) and frustration (from tasks that are too difficult), maximizing neuroplasticity and cognitive gains.
            </p>
          </Card>

          <Card style={{ marginBottom: 'var(--space-6)' }}>
            <h2>Brain Health Score</h2>
            <p style={{ marginBottom: 'var(--space-4)' }}>
              Your Brain Health Score combines two important factors:
            </p>
            <ul style={{ paddingLeft: 'var(--space-6)', marginBottom: 'var(--space-4)' }}>
              <li style={{ marginBottom: 'var(--space-2)' }}>
                <strong>Cognitive Performance (60%)</strong>: Your scores across the three training domains
              </li>
              <li>
                <strong>Lifestyle Factors (40%)</strong>: Exercise, sleep, stress management, and mood
              </li>
            </ul>
            <p style={{ color: 'var(--color-text-secondary)' }}>
              This holistic approach reflects the reality that brain health depends on both cognitive training and healthy lifestyle habits.
            </p>
          </Card>

          <Card>
            <h2>Consistency Matters</h2>
            <p style={{ marginBottom: 'var(--space-4)' }}>
              Research shows that consistent, regular practice produces the best results. We track your streak to encourage daily engagement. Even 15 minutes daily is more effective than sporadic longer sessions.
            </p>
            <p style={{ color: 'var(--color-text-secondary)' }}>
              Your baseline assessment every 6 months provides an objective measure of overall cognitive improvement.
            </p>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default AboutScience;
