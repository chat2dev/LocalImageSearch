# Tests Directory

This directory contains all test and verification related files for the image auto-tagging system.

## Directory Structure

```
tests/
├── docs/                    # Test documentation
│   ├── DOCKER_DEPLOYMENT.md # Docker deployment verification guide
│   └── testing.md           # Testing documentation
├── fixtures/                # Test fixtures and data
│   └── test_images/         # Test images for unit/integration tests
│       ├── create_test_image.py  # Script to create test images
│       ├── test_image_1.jpg      # Test image 1
│       └── test_image_2.jpg      # Test image 2
├── docker-test.sh           # Docker deployment test script
└── test_system.py           # System integration tests
```

## Running Tests

### System Tests

Run the complete system test suite:

```bash
python tests/test_system.py
```

### Docker Deployment Tests

Run Docker deployment verification:

```bash
./tests/docker-test.sh
```

This script will:
1. Build Docker images from scratch
2. Start Ollama and application services
3. Download the qwen3-vl:4b model
4. Run end-to-end deployment verification
5. Verify all 7 test steps pass successfully

For detailed Docker deployment documentation, see:
- `tests/docs/DOCKER_DEPLOYMENT.md`

## Test Fixtures

### Test Images

The `fixtures/test_images/` directory contains sample images used for testing:

- `test_image_1.jpg` - Red gradient test image (512x512)
- `test_image_2.jpg` - Green gradient test image (512x512)

You can generate new test images using:

```bash
python tests/fixtures/test_images/create_test_image.py
```

## Documentation

- `docs/DOCKER_DEPLOYMENT.md` - Complete Docker deployment verification guide
  - Prerequisites and setup
  - 7-step verification workflow
  - Troubleshooting guide
  - Performance notes

- `docs/testing.md` - General testing documentation
  - Test strategy
  - Unit tests
  - Integration tests
  - End-to-end tests

## Notes

- All test paths are relative to the project root
- Test images are excluded from git via .gitignore patterns
- Temporary test files (*.txt, *_report.md, etc.) are automatically ignored
