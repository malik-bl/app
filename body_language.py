class BodyLanguageAnalyzer:
    """
    Analyzes body language signals sent from the frontend.
    The frontend sends computed scores from pixel-analysis + heuristics:
      - eye_contact   : float 0-1  (camera gaze estimate)
      - smile         : float 0-1  (expression positivity)
      - head_stable   : float 0-1  (low movement = high stability)
      - movement      : float 0-1  (pixel diff / motion level)
      - face_visible  : bool       (is a face detected in frame)
    """

    def analyze(self, frame_data: dict) -> dict:
        if not frame_data:
            return self._default_analysis()

        eye_contact  = float(frame_data.get('eye_contact',  0.65))
        smile        = float(frame_data.get('smile',        0.35))
        head_stable  = float(frame_data.get('head_stable',  0.70))
        movement     = float(frame_data.get('movement',     0.20))
        face_visible = bool(frame_data.get('face_visible',  True))

        # Clamp all inputs
        eye_contact = max(0.0, min(1.0, eye_contact))
        smile       = max(0.0, min(1.0, smile))
        head_stable = max(0.0, min(1.0, head_stable))
        movement    = max(0.0, min(1.0, movement))

        # --- Sub-scores (0-100) ---
        eye_score = int(eye_contact * 100)

        # Confidence: weighted combo of head stability and low movement
        movement_penalty = movement * 35
        confidence_score = int(head_stable * 85 + 15 - movement_penalty)
        confidence_score = max(0, min(100, confidence_score))

        # Engagement: smile + eye contact, with face presence bonus
        face_bonus = 8 if face_visible else -10
        engagement_score = int(smile * 30 + eye_contact * 62 + face_bonus)
        engagement_score = max(0, min(100, engagement_score))

        # Overall weighted average
        overall = int(eye_score * 0.38 + confidence_score * 0.37 + engagement_score * 0.25)
        overall = max(0, min(100, overall))

        signals  = []
        feedback = []

        if not face_visible:
            signals.append({"type": "warning", "icon": "👤", "text": "Face not centred in frame"})
            feedback.append("Move closer to the camera and centre your face in the frame")
        else:
            signals.append({"type": "positive", "icon": "✅", "text": "Face clearly visible"})

        if eye_score >= 75:
            signals.append({"type": "positive", "icon": "👁️", "text": "Strong eye contact"})
        elif eye_score >= 50:
            signals.append({"type": "neutral",  "icon": "👁️", "text": "Moderate eye contact"})
            feedback.append("Look directly at the camera lens to show confidence")
        else:
            signals.append({"type": "warning",  "icon": "👁️", "text": "Limited eye contact"})
            feedback.append("Maintain eye contact with the camera — avoid looking down or away")

        if confidence_score >= 75:
            signals.append({"type": "positive", "icon": "🧍", "text": "Stable, confident posture"})
        elif confidence_score >= 50:
            signals.append({"type": "neutral",  "icon": "🧍", "text": "Posture is acceptable"})
            feedback.append("Sit upright and keep shoulders back to project confidence")
        else:
            signals.append({"type": "warning",  "icon": "🧍", "text": "Unstable posture detected"})
            feedback.append("Sit up straight and minimise unnecessary movements")

        if movement > 0.55:
            signals.append({"type": "warning", "icon": "✋", "text": "High movement / fidgeting"})
            feedback.append("Try to stay still — fidgeting signals nervousness to interviewers")
        elif movement < 0.20 and face_visible:
            signals.append({"type": "positive", "icon": "🌟", "text": "Calm and composed"})

        if smile >= 0.55:
            signals.append({"type": "positive", "icon": "😊", "text": "Warm, positive expression"})

        return {
            "overall_score":     overall,
            "eye_contact_score": eye_score,
            "confidence_score":  confidence_score,
            "engagement_score":  engagement_score,
            "signals":           signals[:4],
            "feedback":          feedback[:3],
            "summary":           self._generate_summary(overall, face_visible)
        }

    def _default_analysis(self) -> dict:
        return {
            "overall_score":     68,
            "eye_contact_score": 70,
            "confidence_score":  72,
            "engagement_score":  64,
            "signals": [
                {"type": "neutral", "icon": "📷", "text": "Camera analysis initialising..."}
            ],
            "feedback": [],
            "summary": "Body language analysis in progress"
        }

    def _generate_summary(self, score: int, face_visible: bool) -> str:
        if not face_visible:
            return "Face not detected — please centre yourself in the camera frame"
        if score >= 85:
            return "Excellent presence — confident, engaged, and professional"
        elif score >= 72:
            return "Good body language with minor areas to improve"
        elif score >= 55:
            return "Moderate presence — work on eye contact and reducing movement"
        else:
            return "Body language needs attention — focus on posture and steady gaze"
