export function AnimatedDataBackground() {
  return (
    <div
      aria-hidden="true"
      className="absolute inset-0 animate-gradient-shift opacity-30"
      style={{
        backgroundImage:
          "linear-gradient(135deg, #1a365d 0%, #0d9488 25%, #1a365d 50%, #ea580c 75%, #1a365d 100%)",
        backgroundSize: "300% 300%",
      }}
    />
  );
}
