import { Heart, Lightbulb, ShieldCheck, Search, Cog, BarChart3 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SectionHeading } from "@/components/SectionHeading";

export default function AboutPage() {
  return (
    <div>
      {/* Mission */}
      <section className="bg-primary-900 dark:bg-gray-950 text-white py-20">
        <div className="container mx-auto px-4 text-center max-w-3xl">
          <h1 className="text-4xl sm:text-5xl md:text-5xl font-bold mb-6 opacity-0-init animate-fade-in-up">
            About EDInsights
          </h1>
          <p className="text-lg md:text-xl text-gray-300 leading-relaxed opacity-0-init animate-fade-in-up-delay-1">
            EDInsights.AI is on a mission to revolutionize higher education
            athletics through data-driven intelligence. We empower coaches,
            administrators, and compliance officers with the insights they need
            to elevate programs, protect student-athletes, and achieve
            excellence — on and off the field.
          </p>
        </div>
      </section>

      {/* Core Values */}
      <section className="py-20 dark:bg-gray-900">
        <div className="container mx-auto px-4">
          <SectionHeading
            title="Our Core Values"
            subtitle="The principles that guide every feature we build and every insight we deliver."
          />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                icon: Heart,
                title: "Athlete-First",
                description:
                  "Every insight we deliver is designed to improve outcomes for student-athletes — their performance, well-being, and academic success.",
                color: "from-secondary to-secondary-600",
              },
              {
                icon: Lightbulb,
                title: "Innovation",
                description:
                  "We push the boundaries of sports analytics with cutting-edge AI and machine learning, turning complex data into clear, actionable strategies.",
                color: "from-accent to-accent-700",
              },
              {
                icon: ShieldCheck,
                title: "Integrity",
                description:
                  "Transparency and compliance are built into our DNA. We help programs stay ahead of regulations while building trust with stakeholders.",
                color: "from-primary to-primary-700",
              },
            ].map(({ icon: Icon, title, description, color }, i) => (
              <Card
                key={title}
                className={`overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1 dark:bg-gray-800 dark:border-gray-700 opacity-0-init ${
                  i === 0
                    ? "animate-fade-in-up"
                    : i === 1
                    ? "animate-fade-in-up-delay-1"
                    : "animate-fade-in-up-delay-2"
                }`}
              >
                <div className={`h-1 bg-gradient-to-r ${color}`} />
                <CardHeader>
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-secondary/10 dark:bg-secondary/20 mb-3">
                    <Icon className="h-6 w-6 text-secondary" />
                  </div>
                  <CardTitle className="dark:text-white">{title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">{description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Our Approach */}
      <section className="bg-muted dark:bg-gray-950 py-20">
        <div className="container mx-auto px-4">
          <SectionHeading
            title="Our Approach"
            subtitle="A proven three-step methodology that delivers results."
          />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                icon: Search,
                step: 1,
                title: "Discover",
                description:
                  "We work with your team to understand your unique challenges, data landscape, and goals — ensuring our platform fits seamlessly into your workflow.",
              },
              {
                icon: Cog,
                step: 2,
                title: "Integrate",
                description:
                  "Our platform connects to your existing systems, aggregating data from multiple sources into a unified analytics engine with zero disruption.",
              },
              {
                icon: BarChart3,
                step: 3,
                title: "Transform",
                description:
                  "AI-powered dashboards deliver real-time insights, predictive models, and automated reports that drive smarter decisions across your program.",
              },
            ].map(({ icon: Icon, step, title, description }, i) => (
              <div
                key={step}
                className={`flex flex-col items-center text-center p-6 opacity-0-init ${
                  i === 0
                    ? "animate-fade-in-up"
                    : i === 1
                    ? "animate-fade-in-up-delay-1"
                    : "animate-fade-in-up-delay-2"
                }`}
              >
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-accent text-white text-xl font-bold mb-4 transition-transform duration-200 hover:scale-110">
                  {step}
                </div>
                <div className="flex items-center gap-2 mb-3">
                  <Icon className="h-5 w-5 text-primary dark:text-secondary" />
                  <h3 className="text-xl font-semibold text-primary dark:text-white">
                    {title}
                  </h3>
                </div>
                <p className="text-muted-foreground">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
