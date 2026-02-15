

- **Amazon API Gateway**: REST APIs + WebSocket APIs for real-time voice streaming
- **AWS Lambda**: Serverless compute for all business logic (Node.js 20.x)
  - `voice-handler`: Processes STT output, manages conversation flow
  - `eligibility-matcher`: Executes matching rules against scheme database
  - `response-generator`: Generates contextual Hindi responses
  - `session-manager`: Manages conversation state and context
  - `scheme-query`: Handles scheme data retrieval and filtering
- **AWS Fargate** (optional): For long-running NLU models if Lambda limits exceeded

### Speech & AI Services
- **Amazon Transcribe**: Speech-to-text with custom Hindi vocabulary
  - Custom vocabulary for scheme names, Hindi terms
  - Streaming transcription for real-time interaction
- **Amazon Polly**: Text-to-speech with Aditi voice (Hindi, Indian accent)
  - Neural engine for natural-sounding speech
  - SSML for pronunciation control
- **Amazon Comprehend** (optional): Sentiment analysis, entity extraction
- **Amazon Bedrock** (optional): LLM for response generation (Claude/Llama)
  - Fallback to rule-based generation for cost control

### Data Layer
- **Amazon DynamoDB**: Primary database
  - `schemes` table: Scheme metadata and eligibility rules
  - `sessions` table: Temporary conversation state (TTL: 24h)
  - `user-feedback` table: Anonymous feedback and corrections
- **Amazon S3**: Static content storage
  - Scheme documents (PDFs, images)
  - Audio file cache for common responses
  - Backup and versioning for scheme data
- **Amazon ElastiCache (Redis)**: Caching layer
  - Frequently accessed schemes
  - Session data for ultra-low latency
  - Response templates

### Networking & Security
- **Amazon CloudFront**: CDN for static assets and API acceleration
  - Edge caching for audio responses
  - Reduced latency for rural users
- **AWS WAF**: Web application firewall
  - Rate limiting per IP
  - Bot protection
  - DDoS mitigation
- **AWS Secrets Manager**: Secure credential storage
- **Amazon VPC**: Network isolation for sensitive components

### Monitoring & Operations
- **Amazon CloudWatch**: Logs, metrics, alarms
  - Custom metrics: match accuracy, latency, cost per interaction
  - Log aggregation from all Lambda functions
  - Dashboards for real-time monitoring
- **AWS X-Ray**: Distributed tracing for performance debugging
- **Amazon SNS**: Alerting for critical issues
- **AWS Cost Explorer**: Cost tracking and optimization

### CI/CD & Infrastructure
- **AWS CodePipeline**: Automated deployment pipeline
- **AWS CodeBuild**: Build and test automation
- **AWS CloudFormation** or **AWS CDK**: Infrastructure as code
- **Amazon ECR**: Container registry (if using Fargate)

### Optional/Future Services
- **Amazon Connect**: IVR integration for feature phone support
- **Amazon Pinpoint**: SMS delivery for scheme links
- **Amazon Lex**: Alternative NLU engine (if Bedrock not used)
- **AWS Step Functions**: Complex workflow orchestration

## 3. Data Model

### Scheme Schema (DynamoDB)

```json
{
  "PK": "SCHEME#<scheme_id>",
  "SK": "v<version>",
  "scheme_id": "pm-scholarship-sc-st-2024",
  "name_en": "Post Matric Scholarship for SC Students",
  "name_hi": "अनुसूचित जाति के छात्रों के लिए पोस्ट मैट्रिक छात्रवृत्ति",
  "description_hi": "कक्षा 11 से स्नातकोत्तर तक की पढ़ाई के लिए वित्तीय सहायता",
  "scheme_type": "scholarship",
  "authority": "Ministry of Social Justice and Empowerment",
  "state": "ALL",
  "eligibility_rules": {
    "education_level": ["11th", "12th", "undergraduate", "postgraduate"],
    "category": ["SC"],
    "income_max": 250000,
    "age_min": null,
    "age_max": null,
    "gender": null,
    "state": ["ALL"]
  },
  "benefits": {
    "amount_min": 1000,
    "amount_max": 3000,
    "frequency": "monthly",
    "description_hi": "₹1000 से ₹3000 प्रति माह, कोर्स के अनुसार"
  },
  "documents_required": [
    {
      "name_hi": "आधार कार्ड",
      "name_en": "Aadhaar Card",
      "mandatory": true,
      "alternatives": ["ration_card"]
    },
    {
      "name_hi": "जाति प्रमाण पत्र",
      "name_en": "Caste Certificate",
      "mandatory": true,
      "alternatives": []
    },
    {
      "name_hi": "आय प्रमाण पत्र",
      "name_en": "Income Certificate",
      "mandatory": true,
      "alternatives": []
    },
    {
      "name_hi": "पिछली कक्षा की मार्कशीट",
      "name_en": "Previous Class Marksheet",
      "mandatory": true,
      "alternatives": []
    }
  ],
  "application_process": {
    "mode": "online",
    "portal_url": "https://scholarships.gov.in",
    "steps_hi": [
      "National Scholarship Portal पर जाएं",
      "नया रजिस्ट्रेशन करें",
      "अपनी जानकारी भरें",
      "दस्तावेज़ अपलोड करें",
      "आवेदन सबमिट करें"
    ],
    "helpline": "0120-6619540"
  },
  "deadline": "2024-12-31",
  "tags": ["education", "sc", "post-matric", "central"],
  "priority": 1,
  "active": true,
  "created_at": "2024-01-15T00:00:00Z",
  "updated_at": "2024-02-01T00:00:00Z"
}
```

### Session Schema (DynamoDB with TTL)

```json
{
  "PK": "SESSION#<session_id>",
  "SK": "METADATA",
  "session_id": "uuid-v4",
  "user_context": {
    "education_level": "12th",
    "income": 100000,
    "state": "Bihar",
    "category": "SC",
    "gender": null,
    "age": null
  },
  "conversation_history": [
    {
      "turn": 1,
      "user_input": "Main 12th mein hoon",
      "system_response": "Aapki family ki saalana income kitni hai?",
      "timestamp": "2024-02-15T10:30:00Z"
    }
  ],
  "matched_schemes": [
    {
      "scheme_id": "pm-scholarship-sc-st-2024",
      "confidence": 0.95,
      "matched_at": "2024-02-15T10:32:00Z"
    }
  ],
  "current_state": "collecting_income",
  "language": "hi",
  "ttl": 1708099200,
  "created_at": "2024-02-15T10:30:00Z",
  "last_activity": "2024-02-15T10:32:00Z"
}
```

### Eligibility Rule Structure

Rules are stored as JSON within scheme documents and evaluated by the eligibility engine:

```javascript
// Rule evaluation logic
{
  "rule_type": "AND",  // or "OR"
  "conditions": [
    {
      "field": "education_level",
      "operator": "IN",
      "value": ["11th", "12th", "undergraduate"]
    },
    {
      "field": "income",
      "operator": "LESS_THAN_OR_EQUAL",
      "value": 250000
    },
    {
      "field": "category",
      "operator": "IN",
      "value": ["SC", "ST"]
    },
    {
      "field": "state",
      "operator": "IN",
      "value": ["ALL", "Bihar", "UP"]
    }
  ]
}
```

### Versioning Strategy

- Schemes use composite key: `PK=SCHEME#<id>`, `SK=v<version>`
- Latest version marked with GSI: `GSI1PK=SCHEME#<id>`, `GSI1SK=LATEST`
- Historical versions retained for audit trail
- Version increments on any field change
- Rollback capability via version switching

### Update Pipeline

1. Admin uploads scheme data (CSV/JSON) to S3 bucket
2. S3 event triggers Lambda function
3. Lambda validates schema and data integrity
4. Lambda creates new version in DynamoDB
5. Lambda updates GSI to point to latest version
6. CloudWatch logs all changes
7. SNS notification sent to ops team

## 4. Eligibility Engine Design

### Rule-Based Matching Logic

```javascript
// Pseudo-code for eligibility matching
function matchSchemes(userContext, allSchemes) {
  const matches = [];
  
  for (const scheme of allSchemes) {
    const result = evaluateEligibility(userContext, scheme.eligibility_rules);
    
    if (result.isMatch) {
      matches.push({
        scheme: scheme,
        confidence: result.confidence,
        missingFields: result.missingFields,
        matchedCriteria: result.matchedCriteria
      });
    }
  }
  
  // Sort by confidence, priority, deadline proximity
  return matches.sort((a, b) => {
    if (a.confidence !== b.confidence) return b.confidence - a.confidence;
    if (a.scheme.priority !== b.scheme.priority) return a.scheme.priority - b.scheme.priority;
    return compareDeadlines(a.scheme.deadline, b.scheme.deadline);
  });
}

function evaluateEligibility(userContext, rules) {
  let matchedCriteria = 0;
  let totalCriteria = 0;
  let missingFields = [];
  
  for (const condition of rules.conditions) {
    totalCriteria++;
    
    const userValue = userContext[condition.field];
    
    if (userValue === null || userValue === undefined) {
      missingFields.push(condition.field);
      continue;
    }
    
    const isMatch = evaluateCondition(userValue, condition);
    if (isMatch) matchedCriteria++;
  }
  
  const confidence = totalCriteria > 0 ? matchedCriteria / totalCriteria : 0;
  const isMatch = rules.rule_type === "AND" 
    ? confidence === 1.0 
    : confidence > 0;
  
  return { isMatch, confidence, missingFields, matchedCriteria };
}
```

### Handling Partial Data

- Calculate confidence score based on matched vs. total criteria
- Return partial matches with confidence > 0.5
- Prioritize asking for missing high-impact fields (income, category)
- Allow users to explore partial matches
- Clearly communicate uncertainty: "Aapki di gayi jaankari ke aadhar par..."

### Conflict Resolution

When multiple schemes match with equal confidence:
1. Prioritize by scheme priority field (set by admins)
2. Prioritize schemes with approaching deadlines
3. Prioritize central schemes over state schemes
4. Prioritize higher benefit amounts
5. Present top 3 matches, allow user to explore all

### Confidence Scoring

- **1.0 (100%)**: All criteria matched, no missing data
- **0.8-0.99**: All mandatory criteria matched, optional missing
- **0.5-0.79**: Most criteria matched, some missing
- **< 0.5**: Insufficient match, not shown to user

## 5. Conversation Flow Design

### Multi-Turn Flow in Hindi

```
System: Namaste! Main Boliye-ji hoon. Main aapko sarkari scholarship dhoondhne mein madad karungi.
        Aap kis class mein padhte hain?

User: Main 12th mein hoon

System: Bahut achha! Aapki family ki saalana income kitni hai?

User: Lagbhag 1 lakh

System: Theek hai. Aap kis state se hain?

User: Bihar se

System: Kya aap SC, ST, ya OBC category se belong karte hain?

User: Haan, SC category se

System: [Matching...] 
        Mujhe aapke liye 3 scholarship mili hain. Sabse achhi hai "Post Matric Scholarship for SC Students".
        Is scheme mein aapko har mahine ₹1000 se ₹3000 tak mil sakte hain.
        Kya aap iske baare mein aur jaanna chahenge?

User: Haan, documents kya chahiye?

System: Aapko ye documents chahiye honge:
        1. Aadhaar card
        2. Jati praman patra
        3. Aay praman patra
        4. Pichli class ki marksheet
        
        Kya aap application process ke baare mein jaanna chahte hain?

User: Haan

System: Application online hai. Main aapko SMS bhej rahi hoon jisme website link hoga.
        Steps ye hain:
        1. scholarships.gov.in par jaayein
        2. Naya registration karein
        3. Form bharein
        4. Documents upload karein
        5. Submit karein
        
        Kya aapko koi aur madad chahiye?
```

### Clarification Logic

Trigger clarification when:
- Speech recognition confidence < 70%
- Ambiguous entity (e.g., "thoda kam" for income)
- Out-of-domain response
- Multiple possible interpretations

Clarification strategies:
- Repeat with examples: "Aapki income kitni hai? Jaise 50 hazar, 1 lakh, 2 lakh?"
- Offer choices: "Kya aap (1) SC, (2) ST, ya (3) OBC category se hain?"
- Rephrase: "Matlab aap abhi 12th class mein padhte hain?"

### Fallback Logic

Level 1 - Repeat: "Maaf kijiye, main samjhi nahi. Kya aap phir se bol sakte hain?"
Level 2 - Rephrase: "Shayad maine galat suna. Aap kis class mein padhte hain - 10th, 12th, ya college?"
Level 3 - Skip: "Koi baat nahi, hum ise baad mein bhar sakte hain. Aage chalte hain."
Level 4 - Human handoff: "Mujhe is sawaal mein dikkat ho rahi hai. Kya aap helpline par call kar sakte hain?"

### Retry Handling

- Max 3 retries per question
- After 2 failed attempts, offer alternatives (typing, skip)
- Track retry patterns to improve STT model
- Allow users to go back and correct previous answers

## 6. Edge Case Handling

### Speech Recognition Errors

**Problem**: Background noise, accent variations, unclear speech
**Solution**:
- Use noise cancellation preprocessing
- Custom vocabulary for common Hindi terms
- Confidence threshold: accept only > 70%
- Visual feedback showing transcribed text
- Allow manual correction via text input

### Network Failures

**Problem**: Connection drops mid-conversation
**Solution**:
- Save session state after each turn
- Implement exponential backoff retry
- Queue responses locally, sync when online
- Show offline indicator to user
- Resume conversation from last successful turn

### Ambiguous User Responses

**Problem**: "Haan", "Thoda", "Zyada" without context
**Solution**:
- Maintain conversation context
- Ask follow-up questions
- Provide examples and ranges
- Use slot-filling with confirmation

### No Matching Scheme

**Problem**: User doesn't qualify for any scheme
**Solution**:
- Explain why no matches found
- Suggest nearby matches (e.g., "Agar aapki income thodi kam hoti...")
- Offer to check again with different criteria
- Provide general scholarship search resources
- Collect feedback for scheme database improvement

### Incomplete Information

**Problem**: User doesn't know income, category, etc.
**Solution**:
- Explain why information is needed
- Provide guidance on finding information
- Offer to show partial matches
- Allow skipping optional fields
- Save session for later completion

### Deadline Passed

**Problem**: User finds scheme but deadline has passed
**Solution**:
- Clearly state deadline has passed
- Show next expected deadline if recurring
- Suggest similar active schemes
- Offer to notify when scheme reopens (via SMS)

## 7. Privacy & Security

### Data Minimization

- No account creation required
- No PII stored beyond session (24h TTL)
- Voice recordings deleted immediately after transcription
- Only aggregate analytics collected
- Session IDs are random UUIDs, not linked to users

### Encryption

- TLS 1.3 for all data in transit
- Encryption at rest for DynamoDB (AWS managed keys)
- S3 bucket encryption enabled
- Secrets Manager for API keys and credentials
- No sensitive data in CloudWatch logs

### Consent Handling

- Clear privacy notice on first interaction
- Opt-in for SMS notifications
- Explain data usage in simple Hindi
- Allow users to delete session data
- No tracking across sessions

### Retention Policy

- Session data: 24 hours (DynamoDB TTL)
- Voice recordings: Deleted immediately after STT
- Aggregate metrics: Retained indefinitely (anonymized)
- Error logs: 30 days retention
- Scheme data: Retained with versioning

### Compliance

- Align with Digital Personal Data Protection Act (India)
- No data sharing with third parties
- No cross-border data transfer
- Audit logs for all data access
- Regular security assessments

## 8. Scalability Strategy

### Stateless Services

- All Lambda functions are stateless
- Session state stored in DynamoDB/Redis
- No in-memory state dependencies
- Horizontal scaling without coordination
- Each request can be handled by any instance

### Horizontal Scaling

- Lambda auto-scales to 10,000 concurrent executions
- API Gateway handles millions of requests
- DynamoDB on-demand pricing for auto-scaling
- ElastiCache cluster mode for Redis scaling
- CloudFront edge locations for global distribution

### Caching Strategy

**L1 Cache (Client)**:
- Common audio responses cached locally
- Scheme metadata cached for 1 hour
- Reduces API calls by 30-40%

**L2 Cache (ElastiCache)**:
- Frequently accessed schemes (TTL: 1 hour)
- Session data for active conversations
- Response templates
- Hit rate target: > 80%

**L3 Cache (CloudFront)**:
- Static assets (audio files, images)
- API responses for common queries (TTL: 5 min)
- Edge caching reduces latency by 50%

### Cost Optimization

**Compute**:
- Right-size Lambda memory (512MB-1GB)
- Use Lambda reserved concurrency for predictable workloads
- Batch DynamoDB writes where possible
- Use Fargate Spot for non-critical workloads

**Storage**:
- S3 Intelligent-Tiering for scheme documents
- DynamoDB on-demand for variable traffic
- ElastiCache t3.micro for dev, t3.medium for prod
- Compress audio files (Opus codec)

**Data Transfer**:
- CloudFront reduces origin requests by 70%
- Compress API responses (gzip)
- Use WebSocket for voice streaming (vs. REST polling)
- Regional endpoints to minimize cross-region transfer

**Monitoring**:
- Set CloudWatch alarms for cost thresholds
- Daily cost reports via SNS
- Identify and optimize expensive queries
- Use AWS Cost Anomaly Detection

### Performance Targets

- Cold start: < 1s (Lambda with provisioned concurrency for critical functions)
- Warm start: < 100ms
- DynamoDB read latency: < 10ms (p99)
- ElastiCache latency: < 1ms (p99)
- API Gateway latency: < 50ms (p99)
- End-to-end: < 5s (p95)

## 9. Deployment Architecture

### Multi-Environment Setup

**Dev Environment**:
- Single region (ap-south-1)
- Minimal resources (t3.micro, on-demand)
- Shared DynamoDB tables
- No CloudFront

**Staging Environment**:
- Single region (ap-south-1)
- Production-like configuration
- Separate DynamoDB tables
- CloudFront enabled
- Load testing performed here

**Production Environment**:
- Primary region: ap-south-1 (Mumbai)
- Backup region: ap-south-2 (Hyderabad) - future
- Full redundancy and auto-scaling
- CloudFront with multiple edge locations
- Enhanced monitoring and alerting

### CI/CD Pipeline

1. Code commit to GitHub
2. CodePipeline triggered
3. CodeBuild runs tests and linting
4. Build Lambda deployment packages
5. Deploy to dev environment
6. Run integration tests
7. Manual approval for staging
8. Deploy to staging
9. Run smoke tests
10. Manual approval for production
11. Blue-green deployment to production
12. Monitor for 30 minutes
13. Automatic rollback on errors

### Infrastructure as Code

Using AWS CDK (TypeScript):
- Separate stacks for each component
- Parameterized for multi-environment
- Automated dependency management
- Version controlled in Git
- Automated drift detection

## 10. Monitoring & Observability

### Key Metrics

**Performance**:
- API latency (p50, p95, p99)
- Lambda duration and cold starts
- DynamoDB throttling events
- Cache hit rates

**Business**:
- Conversations started
- Conversations completed
- Schemes matched per user
- SMS click-through rate
- User satisfaction score

**Quality**:
- STT accuracy (word error rate)
- Intent classification accuracy
- Eligibility match relevance
- Error rate by type

**Cost**:
- Cost per interaction
- Daily AWS spend by service
- Cost anomalies

### Alerting Strategy

**Critical (PagerDuty)**:
- API error rate > 5%
- Latency p95 > 10s
- Lambda errors > 10/min
- DynamoDB throttling

**Warning (Email)**:
- Cost increase > 20% day-over-day
- Cache hit rate < 70%
- STT accuracy < 80%

**Info (Dashboard)**:
- Daily usage trends
- Popular schemes
- Geographic distribution

### Logging

- Structured JSON logs from all Lambda functions
- Correlation IDs for request tracing
- PII redaction in logs
- CloudWatch Logs Insights for querying
- 30-day retention for cost optimization

## 11. Testing Strategy

### Unit Tests
- All Lambda functions
- Eligibility matching logic
- Response generation
- Target: > 80% code coverage

### Integration Tests
- API Gateway → Lambda → DynamoDB flows
- STT → Intent extraction → Response generation
- Session management across multiple turns
- Run in staging environment

### Load Tests
- Simulate 10,000 concurrent users
- Sustained load for 1 hour
- Measure latency, error rate, cost
- Use Artillery or Locust

### User Acceptance Testing
- Test with real users (10-20 students)
- Measure completion rate, satisfaction
- Collect feedback on voice quality
- Iterate on conversation flow

### Property-Based Tests
- Eligibility matching correctness
- Rule evaluation logic
- Session state transitions
- Use fast-check or similar

## 12. Future Enhancements

### Phase 2 (Post-Hackathon)
- IVR integration via Amazon Connect
- Support for English and regional languages
- Mobile app (iOS/Android)
- Scheme application tracking
- Push notifications for deadlines

### Phase 3 (Scale)
- AI-powered response generation (Bedrock)
- Personalized scheme recommendations
- Document upload and verification
- Integration with National Scholarship Portal
- Chatbot for text-based interaction

### Phase 4 (Advanced)
- Predictive analytics for scheme matching
- Multi-modal input (voice + image of documents)
- Offline mode with sync
- Community features (Q&A, reviews)
- Admin portal for scheme management
