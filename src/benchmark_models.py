#!/usr/bin/env python3
"""
Model performance benchmark script
Compares auto-tagging accuracy and processing time across different model backends
"""
import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import argparse

from src.image_processor import load_and_preprocess_image, get_image_info
from src.model_factory import create_model
from src.tagging import parse_tags


@dataclass
class BenchmarkResult:
    """Single test result"""
    model_name: str
    model_type: str
    image_path: str
    tags: List[str]
    description: Optional[str]
    processing_time_ms: int
    status: str
    error_message: Optional[str] = None


@dataclass
class ModelConfig:
    """Model configuration"""
    name: str
    model_name: str
    model_type: str
    model_path: str = ""
    api_base: str = ""
    api_key: str = ""
    description: str = ""


class ModelBenchmark:
    """Model benchmark class"""

    def __init__(
        self,
        test_images: List[str],
        tag_count: int = 20,
        generate_description: bool = True,
        language: str = "zh",
        resize_width: int = 512,
        resize_height: int = 512
    ):
        self.test_images = test_images
        self.tag_count = tag_count
        self.generate_description = generate_description
        self.language = language
        self.resize_width = resize_width
        self.resize_height = resize_height
        self.results: List[BenchmarkResult] = []

    def test_model(self, config: ModelConfig) -> List[BenchmarkResult]:
        """
        Test a single model configuration

        Args:
            config: Model configuration

        Returns:
            List of test results
        """
        print(f"\n{'='*60}")
        print(f"Testing model: {config.name}")
        print(f"Type: {config.model_type}")
        if config.description:
            print(f"Description: {config.description}")
        print(f"{'='*60}\n")

        results = []

        try:
            # Create model instance
            model = create_model(
                model_name=config.model_name,
                language=self.language,
                model_type=config.model_type,
                model_path=config.model_path,
                api_base=config.api_base,
                api_key=config.api_key
            )
        except Exception as e:
            print(f"Model initialization failed: {e}")
            for image_path in self.test_images:
                results.append(BenchmarkResult(
                    model_name=config.name,
                    model_type=config.model_type,
                    image_path=image_path,
                    tags=[],
                    description=None,
                    processing_time_ms=0,
                    status="failed",
                    error_message=f"Model initialization failed: {str(e)}"
                ))
            return results

        # Test each image
        for idx, image_path in enumerate(self.test_images, 1):
            print(f"[{idx}/{len(self.test_images)}] Processing: {Path(image_path).name}")

            start_time = time.time()

            try:
                # Load and preprocess image
                image_bytes = load_and_preprocess_image(
                    image_path,
                    self.resize_width,
                    self.resize_height
                )

                if not image_bytes:
                    raise Exception("Failed to load image")

                # Generate tags
                raw_tags = model.generate_tags(image_bytes, self.tag_count)
                tags = parse_tags(raw_tags, self.tag_count)

                # Generate description (optional)
                description = None
                if self.generate_description:
                    description = model.generate_description(image_bytes)
                    if description:
                        description = description.strip()

                processing_time_ms = int((time.time() - start_time) * 1000)

                result = BenchmarkResult(
                    model_name=config.name,
                    model_type=config.model_type,
                    image_path=image_path,
                    tags=tags,
                    description=description,
                    processing_time_ms=processing_time_ms,
                    status="success"
                )

                print(f"  OK Time: {processing_time_ms}ms")
                print(f"  OK Tags: {', '.join(tags[:5])}{'...' if len(tags) > 5 else ''}")

            except Exception as e:
                processing_time_ms = int((time.time() - start_time) * 1000)
                result = BenchmarkResult(
                    model_name=config.name,
                    model_type=config.model_type,
                    image_path=image_path,
                    tags=[],
                    description=None,
                    processing_time_ms=processing_time_ms,
                    status="failed",
                    error_message=str(e)
                )
                print(f"  Failed: {e}")

            results.append(result)

        return results

    def run_benchmark(self, model_configs: List[ModelConfig]) -> Dict[str, Any]:
        """
        Run benchmark tests

        Args:
            model_configs: List of model configurations

        Returns:
            Summary of test results
        """
        all_results = []

        for config in model_configs:
            results = self.test_model(config)
            all_results.extend(results)

        return self._generate_report(all_results, model_configs)

    def _generate_report(self, results: List[BenchmarkResult], configs: List[ModelConfig]) -> Dict[str, Any]:
        """
        Generate test report

        Args:
            results: All test results
            configs: List of model configurations

        Returns:
            Report data
        """
        report = {
            "test_config": {
                "num_images": len(self.test_images),
                "tag_count": self.tag_count,
                "generate_description": self.generate_description,
                "language": self.language,
                "image_size": f"{self.resize_width}x{self.resize_height}"
            },
            "models": []
        }

        # Group and tally by model
        for config in configs:
            model_results = [r for r in results if r.model_name == config.name]

            if not model_results:
                continue

            success_results = [r for r in model_results if r.status == "success"]
            failed_results = [r for r in model_results if r.status == "failed"]

            avg_time = 0
            avg_tags = 0
            if success_results:
                avg_time = sum(r.processing_time_ms for r in success_results) / len(success_results)
                avg_tags = sum(len(r.tags) for r in success_results) / len(success_results)

            model_stats = {
                "name": config.name,
                "type": config.model_type,
                "description": config.description,
                "total_images": len(model_results),
                "success_count": len(success_results),
                "failed_count": len(failed_results),
                "success_rate": len(success_results) / len(model_results) * 100 if model_results else 0,
                "avg_processing_time_ms": int(avg_time),
                "avg_tags_count": round(avg_tags, 1),
                "detailed_results": [asdict(r) for r in model_results]
            }

            report["models"].append(model_stats)

        return report

    def print_report(self, report: Dict[str, Any]):
        """Print test report"""
        print("\n" + "=" * 80)
        print("Benchmark Report")
        print("=" * 80)

        print("\nTest configuration:")
        print(f"  Number of images: {report['test_config']['num_images']}")
        print(f"  Tag count: {report['test_config']['tag_count']}")
        print(f"  Generate description: {report['test_config']['generate_description']}")
        print(f"  Language: {report['test_config']['language']}")
        print(f"  Image size: {report['test_config']['image_size']}")

        print("\nPerformance comparison:")
        print(f"{'Model':<25} {'Type':<10} {'Success':<10} {'Avg Time':<12} {'Avg Tags':<12}")
        print("-" * 80)

        for model in sorted(report['models'], key=lambda x: x['avg_processing_time_ms']):
            print(f"{model['name']:<25} {model['type']:<10} "
                  f"{model['success_rate']:>6.1f}%   "
                  f"{model['avg_processing_time_ms']:>8}ms    "
                  f"{model['avg_tags_count']:>6.1f}")

        print("\nDetailed results:")
        for model in report['models']:
            print(f"\n{model['name']} ({model['type']}):")
            print(f"  Success: {model['success_count']}/{model['total_images']}")
            print(f"  Failed: {model['failed_count']}/{model['total_images']}")
            print(f"  Avg time: {model['avg_processing_time_ms']}ms")
            print(f"  Avg tags: {model['avg_tags_count']}")

            # Show failure details
            failed = [r for r in model['detailed_results'] if r['status'] == 'failed']
            if failed:
                print(f"  Failure reasons:")
                for r in failed[:3]:  # Show at most 3
                    print(f"    - {Path(r['image_path']).name}: {r['error_message']}")

        print("\n" + "=" * 80)

    def save_report(self, report: Dict[str, Any], output_path: str):
        """Save report to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\nReport saved to: {output_path}")


def load_config_file(config_path: str) -> List[ModelConfig]:
    """
    Load model configurations from a JSON config file

    Args:
        config_path: Config file path

    Returns:
        List of model configurations
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    configs = []
    for item in data.get('models', []):
        configs.append(ModelConfig(
            name=item['name'],
            model_name=item['model_name'],
            model_type=item['model_type'],
            model_path=item.get('model_path', ''),
            api_base=item.get('api_base', ''),
            api_key=item.get('api_key', ''),
            description=item.get('description', '')
        ))

    return configs


def get_sample_images(directory: str, count: int = 5) -> List[str]:
    """
    Get sample images from a directory

    Args:
        directory: Image directory
        count: Number of samples

    Returns:
        List of image paths
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
    image_files = []

    path = Path(directory)
    if path.is_file():
        return [str(path)]

    for ext in image_extensions:
        image_files.extend(path.glob(f"*{ext}"))
        image_files.extend(path.glob(f"*{ext.upper()}"))

    image_files = sorted(image_files)[:count]
    return [str(f) for f in image_files]


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Model performance benchmark')
    parser.add_argument('--config', type=str, help='Model config file path (JSON format)')
    parser.add_argument('--images', type=str, required=True, help='Test image directory or file path')
    parser.add_argument('--count', type=int, default=5, help='Number of test images (default: 5)')
    parser.add_argument('--tag-count', type=int, default=20, help='Tag count (default: 20)')
    parser.add_argument('--language', type=str, default='zh', choices=['en', 'zh', 'ja', 'ko', 'es', 'fr', 'de', 'ru'], help='Language (default: zh)')
    parser.add_argument('--description', action='store_true', help='Generate description')
    parser.add_argument('--no-description', dest='description', action='store_false', help='Do not generate description')
    parser.add_argument('--resize', type=str, default='512x512', help='Image resize (default: 512x512)')
    parser.add_argument('--output', type=str, default='benchmark_report.json', help='Output report path (default: benchmark_report.json)')
    parser.set_defaults(description=True)

    args = parser.parse_args()

    # Parse image resize dimensions
    try:
        width, height = map(int, args.resize.split('x'))
    except ValueError:
        print("Error: Image resize format should be WIDTHxHEIGHT, e.g. 512x512")
        sys.exit(1)

    # Get test images
    test_images = get_sample_images(args.images, args.count)
    if not test_images:
        print(f"Error: No test images found: {args.images}")
        sys.exit(1)

    print(f"Found {len(test_images)} test images")

    # Load model configurations
    if args.config:
        model_configs = load_config_file(args.config)
    else:
        # Use default configuration (Ollama only)
        print("\nNo config file specified, using default Ollama configuration")
        print("Tip: Use --config to specify a config file for testing multiple models\n")
        model_configs = [
            ModelConfig(
                name="Qwen3-VL-4B (Ollama)",
                model_name="qwen3-vl:4b",
                model_type="ollama",
                description="OllamaDefault configuration"
            )
        ]

    if not model_configs:
        print("Error: No model configurations found")
        sys.exit(1)

    print(f"Will test {len(model_configs)} model configuration(s)\n")

    # Create benchmark instance
    benchmark = ModelBenchmark(
        test_images=test_images,
        tag_count=args.tag_count,
        generate_description=args.description,
        language=args.language,
        resize_width=width,
        resize_height=height
    )

    # Run benchmark
    report = benchmark.run_benchmark(model_configs)

    # Print report
    benchmark.print_report(report)

    # Save report
    benchmark.save_report(report, args.output)


if __name__ == "__main__":
    main()
