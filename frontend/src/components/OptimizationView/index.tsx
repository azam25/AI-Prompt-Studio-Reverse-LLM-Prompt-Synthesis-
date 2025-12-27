import './OptimizationView.css';

export function OptimizationView() {
    return (
        <div className="optimization-view">
            <div className="optimization-header">
                <h3 className="section-title">
                    <span className="section-title-icon">⚡</span>
                    RLAIF Optimization
                </h3>
                <span className="status-badge loading">Running</span>
            </div>

            <div className="optimization-progress">
                <div className="progress-animation">
                    <div className="spinner spinner-lg"></div>
                </div>

                <div className="progress-info">
                    <h4>Optimizing Prompt...</h4>
                    <p>Running iterative refinement with AI feedback</p>
                </div>

                <div className="progress-steps">
                    <div className="step active">
                        <span className="step-icon">1</span>
                        <span className="step-text">Analyzing Template</span>
                    </div>
                    <div className="step">
                        <span className="step-icon">2</span>
                        <span className="step-text">Designing Query</span>
                    </div>
                    <div className="step">
                        <span className="step-icon">3</span>
                        <span className="step-text">Retrieving Context</span>
                    </div>
                    <div className="step">
                        <span className="step-icon">4</span>
                        <span className="step-text">Evaluating Output</span>
                    </div>
                    <div className="step">
                        <span className="step-icon">5</span>
                        <span className="step-text">Refining Query</span>
                    </div>
                </div>
            </div>

            <div className="optimization-note">
                <p>🔄 The optimization loop runs a minimum of 3 iterations to ensure quality.</p>
                <p>Each iteration evaluates and refines the query based on AI feedback.</p>
            </div>
        </div>
    );
}
