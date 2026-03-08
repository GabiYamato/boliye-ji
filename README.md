# Hindi Voice Agent for Government Schemes 🇮🇳

A Hindi-speaking voice agent that helps students discover government scholarships and schemes through phone calls. Built with BentoML, Pipecat, and open-source models.

## Overview

This voice agent accepts phone calls via Twilio and responds to user queries in Hindi about government schemes and scholarships. It uses function calling to check eligibility, collect information, and provide detailed scheme information.

## Features

- **Hindi Voice Interaction**: Natural Hindi conversation using XTTS TTS and Whisper STT
- **Function Calling**: LLM can call 3 functions:
  1. **check_eligibility** - Check eligibility for government schemes based on category, income, education
  2. **collect_user_info** - Collect student information (name, age, state, education)
  3. **get_scheme_details** - Get detailed scheme information (eligibility, documents, amount)
- **Twilio Integration**: Accessible via phone number
- **Small Model**: Uses <8B parameter LLM (Llama 3.1 8B) that runs on 8GB GPU (RTX 4060)
- **4 Government Schemes**: Pre-loaded with dummy data for testing

## Files

- `hindi_voice_service.py` - Main BentoML service with Twilio WebSocket integration
- `hindi_bot_logic.py` - Bot logic with function calling and Pipecat pipeline
- `test_functions.py` - Standalone test script (no external services needed)
- `requirements.txt` - Python dependencies
- `bentofile.yaml` - BentoML deployment configuration

## Quick Start

### 1. Test Functions (No Setup Required)

```bash
python test_functions.py
```

This tests all 3 functions and shows Hindi responses - perfect for verifying the output!

### 2. Run Full Service

See [SETUP.md](SETUP.md) for detailed setup instructions.

## Function Examples

### Check Eligibility
**User**: "मैं एससी कैटेगरी से हूं, मेरी आय दो लाख रुपये है"

**Response**: "आपकी पात्रता के अनुसार, आप निम्नलिखित योजनाओं के लिए आवेदन कर सकते हैं: प्री-मैट्रिक स्कॉलरशिप योजना, एससीएसटी छात्रवृत्ति योजना..."

### Collect Info
**User**: "मेरा नाम राज है, मैं 17 साल का हूं, बिहार से हूं"

**Response**: "धन्यवाद! मैंने आपकी जानकारी सहेज ली है। आपका नाम राज है, आपकी उम्र 17 वर्ष है..."

### Get Scheme Details
**User**: "पोस्ट मैट्रिक स्कॉलरशिप के बारे में बताओ"

**Response**: "पोस्ट-मैट्रिक स्कॉलरशिप योजना दसवीं कक्षा के बाद की पढ़ाई के लिए है। इसमें बीस हजार से पचास हजार रुपये मिलते हैं..."

## Architecture

```
Phone Call → Twilio → WebSocket
                ↓
         BentoML Service
                ↓
         Pipecat Pipeline:
    VAD → STT (Whisper) → LLM (Llama 3.1 8B)
                ↓
         Function Calling:
    - check_eligibility()
    - collect_user_info()
    - get_scheme_details()
                ↓
    TTS (XTTS Hindi) → Twilio → Phone
```

## Hardware Requirements

- NVIDIA GPU with 8GB VRAM (e.g., RTX 4060)
- CUDA 11.8+
- Python 3.11

## Included Schemes

1. **प्री-मैट्रिक स्कॉलरशिप** - For class 1-10 students
2. **पोस्ट-मैट्रिक स्कॉलरशिप** - For college students
3. **एससीएसटी छात्रवृत्ति** - For SC/ST students
4. **मेरिट कम मीन्स** - Merit-based scholarship

Each scheme includes details on eligibility, documents, and amounts in clear Hindi.

## External Services Required

1. **LLM Service** - Llama 3.1 8B (via BentoVLLM or Ollama)
2. **XTTS Service** - Hindi text-to-speech (via BentoXTTSStreaming)

See [SETUP.md](SETUP.md) for deployment instructions.

## License

Demonstration project for government scheme assistance.
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
