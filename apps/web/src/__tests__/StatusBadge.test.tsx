import { render, screen } from "@testing-library/react";
import { StatusBadge } from "@/components/common/StatusBadge";

describe("StatusBadge", () => {
  it("renders severity badges", () => {
    render(<StatusBadge type="severity" value="critical" />);
    expect(screen.getByText("critical")).toBeInTheDocument();
  });

  it("renders status badges", () => {
    render(<StatusBadge type="status" value="in_progress" />);
    expect(screen.getByText("in progress")).toBeInTheDocument();
  });

  it("renders health badges", () => {
    render(<StatusBadge type="health" value="degraded" />);
    expect(screen.getByText("degraded")).toBeInTheDocument();
  });

  it("applies correct CSS for critical severity", () => {
    const { container } = render(<StatusBadge type="severity" value="critical" />);
    expect(container.firstChild).toHaveClass("badge-critical");
  });
});
