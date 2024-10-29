from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from time import sleep
import random

console = Console()


def print_docker_build_output():
    # Initialize progress with building timer on top
    with Progress(
        SpinnerColumn(),
        # TextColumn("[green][+] Building {task.elapsed:.1f}s (12/17)"),
        # TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        building_task = progress.add_task("docker:default", total=None)

        # Define the static build steps and dim log lines
        build_steps = [
            "[dim] => CACHED [builder 3/7] COPY go.mod go.sum ./                                            0.0s",
            " => [builder 4/7] COPY ./manager/ ./manager/                                                   0.6s",
            " => [builder 5/7] COPY ./operator/api ./operator/api                                           0.0s",
            " => [builder 6/7] COPY ./pkg/ ./pkg                                                            0.1s",
            " => [builder 7/7] RUN go build -o bin/manager ./manager/cmd/main.go                          605.0s",
        ]

        download_logs = [
            "[dim] => => # go: downloading github.com/Shopify/sarama v1.38.1",
            "[dim] => => # go: downloading github.com/confluentinc/confluent-kafka-go/v2 v2.5.4",
            "[dim] => => # go: downloading github.com/cloudevents/sdk-go/protocol/kafka_confluent/v2 v2.0.0",
            "[dim] => => # go: downloading github.com/cloudevents/sdk-go/protocol/kafka_sarama/v2 v2.13.0",
            "[dim] => => # go: downloading github.com/imdario/mergo v0.3.16",
            "[dim] => => # go: downloading golang.org/x/term v0.24.0",
        ]

        while not progress.finished:
            # Retrieve the elapsed time directly from the task
            elapsed_time = progress.tasks[building_task].elapsed

            # Clear the console and print the formatted output
            console.clear()
            console.print(
                f"[green][+] Building {elapsed_time:.2f}s (12/17)                                                                                                         docker:default"
            )

            # # Print the formatted build steps
            # for step in build_steps:
            #     console.print(step)

            # Show a few randomly chosen download logs, simulating log updates
            for log in random.sample(download_logs, 4):
                console.print(log)

            # Simulate progression in build time and tasks
            sleep(1)
            # progress.advance(building_task, random.uniform(0.5, 2.5))
            # progress.stop()


# Run the output function
print_docker_build_output()
