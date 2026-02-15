# Boliye-ji - Requirements Document

## 1. Overview

### Problem Statement
Millions of Indian students, especially in rural areas, miss out on government scholarships and welfare schemes due to:
- Complex eligibility criteria spread across multiple schemes
- Language barriers (most information in English)
- Low digital literacy preventing effective online research
- Lack of awareness about available schemes
- Difficulty understanding application requirements

### Target Users
- Rural students (Classes 8-12, undergraduate)
- Urban low-income students
- First-generation learners
- Students with limited English proficiency
- Students with limited smartphone/internet experience

### Goals
- Enable voice-first discovery of relevant scholarships in Hindi
- Simplify eligibility checking through guided conversation
- Provide clear, actionable information about schemes
- Reduce time from discovery to application submission
- Work on low-bandwidth connections
- Require minimal digital literacy

### Non-Goals
- Not a scholarship application submission platform
- Not providing financial advice beyond scheme information
- Not storing personal user data long-term
- Not supporting languages other than Hindi (v1)
- Not handling scheme creation or government-side workflows

## 2. User Personas

### Persona 1: Priya - Rural Student
- Age: 16, Class 11 student in Uttar Pradesh
- Family income: ₹80,000/year (farming)
- First smartphone user in family
- Comfortable speaking Hindi, limited English
- 2G/3G internet connectivity
- Needs: Post-matric scholarship for SC category

### Persona 2: Rahul - Urban Low-Income Student
- Age: 19, first-year engineering student in Pune
- Family income: ₹2,50,000/year
- Moderate digital literacy
- Speaks Hindi and English
- 4G connectivity but limited data plan
- Needs: Merit-cum-means scholarship, education loan schemes

### Persona 3: Sunita - First-Generation Learner
- Age: 21, pursuing B.Ed in Rajasthan
- Family income: ₹1,20,000/year
- Parents illiterate, she's first to attend college
- Comfortable with voice but not typing
- Intermittent internet access
- Needs: Women-specific schemes, minority scholarships

## 3. User Journeys

### Journey 1: First-Time Interaction
1. User opens app/calls IVR number
2. System greets in Hindi, explains purpose
3. System asks: "Aap kis class mein padhte hain?" (education level)
4. User responds: "Main 12th mein hoon"
5. System asks: "Aapki family ki saalana income kitni hai?"
6. User responds: "Lagbhag 1 lakh"
7. System asks: "Aap kis state se hain?"
8. User responds: "Bihar"
9. System asks: "Kya aap SC/ST/OBC category se belong karte hain?"
10. User responds: "Haan, SC"
11. System matches 3 schemes, explains top match
12. User asks: "Documents kya chahiye?"
13. System lists required documents
14. User asks: "Apply kaise karein?"
15. System explains application steps
16. System offers to send SMS with scheme links

### Journey 2: Returning User
1. User returns with specific question
2. System recognizes context (if session active)
3. User asks: "Mujhe engineering ke liye scholarship chahiye"
4. System asks clarifying questions (only missing info)
5. System provides targeted results
6. User explores multiple schemes via voice

### Journey 3: Incomplete Eligibility Flow
1. User starts conversation
2. Provides partial information (education, state)
3. Connection drops or user exits
4. User returns later
5. System offers to continue or restart
6. System shows partial matches with confidence levels
7. User completes remaining questions
8. System refines matches

## 4. Functional Requirements

### FR1: Voice Input in Hindi
- Accept spoken Hindi input via microphone
- Support common Hindi dialects (Khari Boli, Awadhi, Bhojpuri variations)
- Handle code-mixing (Hindi-English)
- Tolerate background noise in rural settings
- Support both formal and colloquial Hindi

### FR2: Guided Question Flow
- Ask questions in logical sequence
- Adapt flow based on previous answers
- Skip irrelevant questions (e.g., gender if scheme doesn't require)
- Allow users to go back and change answers
- Provide examples for unclear questions
- Confirm understanding before proceeding

### FR3: Eligibility Matching Engine
- Match user profile against 50+ central and state schemes
- Apply AND/OR logic for complex eligibility rules
- Handle range-based criteria (income brackets, age ranges)
- Support partial matching with confidence scores
- Prioritize schemes by relevance and deadline proximity

### FR4: Scheme Explanation Generation
- Explain scheme benefits in simple Hindi
- Break down complex terms (e.g., "post-matric" → "10th ke baad")
- Provide amount/benefit details
- Mention application deadlines
- Highlight unique advantages

### FR5: Document Checklist Output
- List required documents in Hindi
- Explain where to obtain each document
- Indicate if document is mandatory or optional
- Provide alternatives (e.g., "Aadhaar ya ration card")

### FR6: Application Steps Guidance
- Provide step-by-step application process
- Include website URLs (sent via SMS)
- Mention offline application options if available
- Warn about common mistakes
- Provide helpline numbers

### FR7: Error Handling
- Gracefully handle speech recognition failures
- Ask for clarification on ambiguous input
- Provide fallback options (repeat, rephrase, skip)
- Allow manual correction of misunderstood information
- Maintain conversation context across errors

### FR8: Low-Bandwidth Operation
- Minimize data transfer per interaction
- Cache common responses locally
- Support audio compression
- Provide text-only fallback mode
- Work on 2G/3G networks

## 5. Non-Functional Requirements

### NFR1: Latency Targets
- Speech-to-text: < 2 seconds
- Eligibility matching: < 1 second
- Response generation: < 1 second
- Text-to-speech: < 2 seconds
- End-to-end response: < 5 seconds (p95)

### NFR2: Availability
- 99.5% uptime during business hours (8 AM - 8 PM IST)
- 99% uptime overall
- Graceful degradation during AWS service issues
- Automatic failover for critical components

### NFR3: Scalability
- Support 10,000 concurrent users (hackathon demo)
- Scale to 100,000 concurrent users (production)
- Handle 1M+ scheme queries per day
- Auto-scale based on traffic patterns

### NFR4: Security
- Encrypt voice data in transit (TLS 1.3)
- No persistent storage of voice recordings
- Anonymize any logged user data
- Comply with Indian data protection norms
- Secure API endpoints with authentication

### NFR5: Accessibility
- Voice-first design (no typing required)
- Support for users with visual impairments
- Simple language (5th-grade reading level equivalent)
- No complex navigation required
- Work on entry-level smartphones

### NFR6: Cost Constraints
- Target: < ₹0.50 per user interaction
- Optimize AWS service usage
- Use spot instances where possible
- Implement aggressive caching
- Monitor and alert on cost anomalies

## 6. Constraints

### Technical Constraints
- Must use AWS services exclusively (hackathon requirement)
- Must support Hindi language (primary)
- Must work on mobile web (no app store dependency for v1)
- Must handle intermittent connectivity
- Must minimize client-side processing

### Data Constraints
- No long-term storage of personal information
- Scheme data must be versioned and auditable
- Must support manual scheme updates by admins
- Session data retained for max 24 hours

### Design Constraints
- Voice-first, not voice-only (provide visual feedback)
- Assume low digital literacy
- Assume limited English proficiency
- Design for small screens (< 6 inches)
- Support feature phones via IVR (future)

## 7. Success Metrics

### Primary Metrics
- **Scheme Match Accuracy**: > 90% of matches are relevant to user
- **Completion Rate**: > 70% of users complete eligibility flow
- **Voice Recognition Accuracy**: > 85% word accuracy for Hindi
- **Average Response Latency**: < 5 seconds end-to-end

### Secondary Metrics
- User satisfaction score: > 4/5
- Repeat usage rate: > 30% within 30 days
- SMS link click-through rate: > 40%
- Error recovery rate: > 80% of errors recovered without restart

### Business Metrics
- Cost per interaction: < ₹0.50
- Daily active users: Track growth
- Schemes discovered per user: > 2 average
- Geographic reach: Coverage across 20+ states

## 8. Acceptance Criteria

### AC1: Voice Interaction
- User can complete full eligibility flow using only voice
- System correctly transcribes Hindi speech in 85%+ cases
- System responds with natural-sounding Hindi speech

### AC2: Eligibility Matching
- System matches at least 1 relevant scheme for 80%+ of users
- System correctly applies all eligibility rules
- System handles edge cases (boundary values, missing data)

### AC3: Information Quality
- Scheme information is accurate and up-to-date
- Document lists are complete and correct
- Application steps are clear and actionable

### AC4: Performance
- System responds within 5 seconds for 95% of queries
- System handles 10,000 concurrent users without degradation
- System maintains 99.5% uptime during demo period

### AC5: Usability
- Users with no prior app experience can complete flow
- Users understand system responses without confusion
- Users can recover from errors without assistance

### AC6: Cost Efficiency
- System operates within ₹0.50 per interaction budget
- AWS costs are predictable and monitored
- No unexpected cost spikes during load
