import { render, screen } from "@testing-library/react";
import { MetricCard } from "@/components/common/MetricCard";

describe("MetricCard", () => {
  it("renders title and value", () => {
    render(<MetricCard title="Open Incidents" value={42} />);
    expect(screen.getByText("Open Incidents")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
  });

  it("renders subtitle when provided", () => {
    render(<MetricCard title="Test" value={100} subtitle="of 200 services" />);
    expect(screen.getByText("of 200 services")).toBeInTheDocument();
  });

  it("renders positive trend with up arrow", () => {
    render(<MetricCard title="Test" value={5} trend={{ value: 12, label: "vs last week" }} />);
    expect(screen.getByText(/12%/)).toBeInTheDocument();
    expect(screen.getByText("vs last week")).toBeInTheDocument();
  });

  it("renders negative trend with down arrow", () => {
    render(<MetricCard title="Test" value={5} trend={{ value: -8, label: "vs yesterday" }} />);
    expect(screen.getByText(/8%/)).toBeInTheDocument();
  });
});
