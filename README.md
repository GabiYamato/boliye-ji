# Boliye-ji 🎓

A voice-first scholarship discovery platform helping Indian students find government schemes through natural Hindi conversations.

## Problem

Millions of Indian students, especially in rural areas, miss out on government scholarships due to:
- Complex eligibility criteria across multiple schemes
- Language barriers (most information in English)
- Low digital literacy preventing effective online research
- Lack of awareness about available schemes

## Solution

Boliye-ji enables students to discover relevant scholarships through simple voice conversations in Hindi. Just speak naturally, and the system guides you through eligibility checking and provides actionable information about schemes you qualify for.

## Key Features

- Voice-first interaction in Hindi (no typing required)
- Guided conversation flow with smart questions
- Real-time eligibility matching across 50+ schemes
- Simple explanations of benefits and requirements
- Document checklists in Hindi
- Step-by-step application guidance
- SMS delivery of scheme links
- Works on low-bandwidth 2G/3G connections

## Target Users

- Rural students (Classes 8-12, undergraduate)
- Urban low-income students
- First-generation learners
- Students with limited English proficiency
- Students with minimal smartphone experience

## How It Works

1. User opens the app and speaks in Hindi
2. System asks guided questions about education, income, category, state
3. Eligibility engine matches user profile against scheme database
4. System explains relevant schemes in simple Hindi
5. User can ask about documents, application process, deadlines
6. System sends SMS with scheme links for easy access

## Technology Stack

### AWS Services
- **Amazon Transcribe**: Speech-to-text with custom Hindi vocabulary
- **Amazon Polly**: Text-to-speech with natural Hindi voice (Aditi)
- **AWS Lambda**: Serverless compute for business logic
- **Amazon DynamoDB**: Scheme database and session management
- **Amazon API Gateway**: REST and WebSocket APIs
- **Amazon ElastiCache**: Redis caching for performance
- **Amazon CloudFront**: CDN for low-latency delivery
- **Amazon S3**: Static content and scheme documents
- **Amazon CloudWatch**: Monitoring and logging
- **AWS Bedrock** (optional): LLM for response generation

### Architecture Highlights
- Serverless and auto-scaling
- Voice streaming via WebSocket
- Sub-5 second response time
- Cost-optimized (< ₹0.50 per interaction)
- 99.5% uptime target

## Performance Targets

- Speech-to-text: < 2 seconds
- Eligibility matching: < 1 second
- End-to-end response: < 5 seconds (p95)
- Voice recognition accuracy: > 85%
- Scheme match accuracy: > 90%
- Completion rate: > 70%

## Getting Started

### Prerequisites
- AWS Account with appropriate permissions
- Node.js 20.x
- AWS CLI configured
- AWS CDK installed

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/boliye-ji.git
cd boliye-ji

# Install dependencies
npm install

# Deploy infrastructure
npm run deploy:dev
```

### Configuration

Set up environment variables:
```bash
export AWS_REGION=ap-south-1
export ENVIRONMENT=dev
```

### Running Locally

```bash
# Start local development server
npm run dev

# Run tests
npm test

# Run integration tests
npm run test:integration
```

## Project Structure

```
boliye-ji/
├── infrastructure/       # AWS CDK infrastructure code
├── lambda/              # Lambda function handlers
│   ├── voice-handler/
│   ├── eligibility-matcher/
│   ├── response-generator/
│   └── session-manager/
├── data/                # Scheme data and rules
├── tests/               # Unit and integration tests
└── docs/                # Additional documentation
```

## Data Model

### Scheme Structure
Each scheme contains:
- Eligibility rules (education, income, category, state)
- Benefits and amounts
- Required documents
- Application process steps
- Deadlines and priority

### Session Management
- Temporary conversation state (24h TTL)
- User context (education, income, category, state)
- Matched schemes with confidence scores
- No long-term PII storage

## Privacy & Security

- No account creation required
- Voice recordings deleted immediately after transcription
- Session data retained for max 24 hours
- TLS 1.3 encryption for all data in transit
- Compliant with Indian data protection norms
- No PII in logs or analytics

## Cost Optimization

- Lambda right-sizing and reserved concurrency
- Aggressive caching (client, Redis, CloudFront)
- Audio compression (Opus codec)
- DynamoDB on-demand pricing
- S3 Intelligent-Tiering
- Target: < ₹0.50 per user interaction

## Monitoring

Key metrics tracked:
- API latency and error rates
- STT/TTS accuracy
- Eligibility match relevance
- User completion rates
- Cost per interaction
- Geographic distribution

## Testing

```bash
# Unit tests
npm test

# Integration tests
npm run test:integration

# Load tests (10,000 concurrent users)
npm run test:load

# User acceptance tests
npm run test:uat
```

## Deployment

### Environments
- **Dev**: Single region, minimal resources
- **Staging**: Production-like, for testing
- **Production**: Full redundancy, auto-scaling

### CI/CD Pipeline
1. Code commit triggers pipeline
2. Automated tests and linting
3. Deploy to dev environment
4. Manual approval for staging
5. Smoke tests in staging
6. Manual approval for production
7. Blue-green deployment
8. Automated rollback on errors

## Future Roadmap

### Phase 2
- IVR integration for feature phones
- Support for English and regional languages
- Mobile apps (iOS/Android)
- Scheme application tracking

### Phase 3
- AI-powered response generation
- Personalized recommendations
- Document upload and verification
- Integration with National Scholarship Portal

### Phase 4
- Predictive analytics
- Multi-modal input (voice + images)
- Offline mode with sync
- Community features

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

Built for AWS Hackathon 2024 to empower Indian students with better access to education opportunities.

## Contact

For questions or support:
- Email: support@boliye-ji.in
- GitHub Issues: [github.com/your-org/boliye-ji/issues](https://github.com/your-org/boliye-ji/issues)

---

Made with ❤️ for Indian students
