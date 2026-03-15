import Link from "next/link";
import {
  ArrowRight,
  TrendingUp,
  Target,
  LayoutDashboard,
  Cpu,
  BrainCircuit,
  ScanSearch,
  Database,
  Cog,
  Lightbulb,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { SectionHeading } from "@/components/SectionHeading";
import { ValueCard } from "@/components/ValueCard";
import { AnimatedDataBackground } from "@/components/AnimatedDataBackground";
import { DataDots } from "@/components/DataDots";
import { StatsPreview } from "@/components/StatsPreview";

export default function HomePage() {
  return (
    <div>
      {/* Hero */}
      <section className="relative bg-primary-900 dark:bg-gray-950 text-white py-24 overflow-hidden">
        <AnimatedDataBackground />
        <DataDots />
        <div className="container relative z-10 mx-auto px-4 text-center">
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold mb-6 leading-tight opacity-0-init animate-fade-in-up">
            Empowered Data.{" "}
            <span className="text-accent">AI Insights.</span>{" "}
            <br className="hidden md:block" />
            Real Results.
          </h1>
          <p className="text-lg md:text-xl text-gray-300 mb-10 max-w-2xl mx-auto opacity-0-init animate-fade-in-up-delay-1">
            Transform your sports analytics with our cutting-edge AI platform.
            Unlock performance data that drives winning strategies.
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-4 opacity-0-init animate-fade-in-up-delay-2">
            <Link href="/signup">
              <Button
                size="lg"
                className="bg-accent hover:bg-accent-700 text-lg px-8 transition-transform duration-200 hover:scale-105"
              >
                Get Started <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link href="/about">
              <Button
                size="lg"
                variant="outline"
                className="bg-transparent text-white border-white hover:bg-white/10 hover:text-white text-lg px-8 transition-transform duration-200 hover:scale-105"
              >
                Learn More
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Vision / Value Cards */}
      <section className="py-20 dark:bg-gray-900">
        <div className="container mx-auto px-4">
          <SectionHeading
            title="Driving Athletic Excellence"
            subtitle="Our platform delivers measurable impact across every dimension of sports performance."
          />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <ValueCard
              icon={TrendingUp}
              title="Enhanced Performance"
              stat="37%"
              description="Average improvement in key performance metrics for teams using our analytics platform."
              className="opacity-0-init animate-fade-in-up"
            />
            <ValueCard
              icon={Target}
              title="Strategic Advantage"
              stat="86%"
              description="Of coaches report better game-day decisions with AI-powered scouting and strategy tools."
              className="opacity-0-init animate-fade-in-up-delay-1"
            />
            <ValueCard
              icon={LayoutDashboard}
              title="Complete Dashboard"
              stat="12K+"
              description="Data points tracked per athlete per season, delivering a comprehensive performance picture."
              className="opacity-0-init animate-fade-in-up-delay-2"
            />
          </div>
        </div>
      </section>

      {/* Platform Preview */}
      <StatsPreview />

      {/* Technology */}
      <section className="relative bg-primary-900 dark:bg-gray-950 text-white py-20 overflow-hidden">
        {/* Grid pattern overlay */}
        <div
          aria-hidden="true"
          className="absolute inset-0 opacity-5"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)",
            backgroundSize: "40px 40px",
          }}
        />
        <div className="container relative z-10 mx-auto px-4">
          <SectionHeading
            title="Powered by Advanced Technology"
            subtitle="We combine modern AI and machine learning to turn raw data into winning strategies."
            light
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-start">
            {/* Capabilities */}
            <div className="space-y-6 opacity-0-init animate-fade-in-up">
              <h3 className="text-xl font-semibold text-secondary mb-4">
                Core Capabilities
              </h3>
              {[
                { icon: Cpu, text: "Python & AI-Driven Processing" },
                { icon: BrainCircuit, text: "Machine Learning Models" },
                { icon: ScanSearch, text: "Real-Time Pattern Detection" },
              ].map(({ icon: Icon, text }) => (
                <div key={text} className="flex items-center gap-4 group">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-secondary/20 transition-colors duration-200 group-hover:bg-secondary/30">
                    <Icon className="h-5 w-5 text-secondary" />
                  </div>
                  <span className="text-lg">{text}</span>
                </div>
              ))}
            </div>

            {/* Numbered Steps */}
            <div className="space-y-6 opacity-0-init animate-fade-in-up-delay-1">
              <h3 className="text-xl font-semibold text-secondary mb-4">
                How It Works
              </h3>
              {[
                { icon: Database, step: 1, title: "Collection", desc: "Aggregate data from multiple sources seamlessly." },
                { icon: Cog, step: 2, title: "Processing", desc: "Clean, normalize, and enrich data at scale." },
                { icon: Lightbulb, step: 3, title: "Insights", desc: "Deliver actionable intelligence to your team." },
              ].map(({ icon: Icon, step, title, desc }) => (
                <div key={step} className="flex items-start gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent text-white font-bold transition-transform duration-200 hover:scale-110">
                    {step}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <Icon className="h-4 w-4 text-secondary" />
                      <span className="font-semibold text-lg">{title}</span>
                    </div>
                    <p className="text-gray-300 mt-1">{desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
