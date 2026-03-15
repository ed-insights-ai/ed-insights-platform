const dots = [
  { left: "10%", top: "20%", size: 6, delay: "0s" },
  { left: "25%", top: "60%", size: 4, delay: "1s" },
  { left: "40%", top: "30%", size: 8, delay: "2s" },
  { left: "55%", top: "70%", size: 5, delay: "0.5s" },
  { left: "70%", top: "15%", size: 7, delay: "3s" },
  { left: "85%", top: "50%", size: 4, delay: "1.5s" },
  { left: "15%", top: "80%", size: 6, delay: "4s" },
  { left: "60%", top: "45%", size: 3, delay: "2.5s" },
  { left: "90%", top: "75%", size: 5, delay: "3.5s" },
  { left: "35%", top: "10%", size: 4, delay: "5s" },
];

export function DataDots() {
  return (
    <div aria-hidden="true" className="absolute inset-0 overflow-hidden">
      {dots.map((dot, i) => (
        <span
          key={i}
          className="absolute rounded-full bg-white animate-float-dot"
          style={{
            left: dot.left,
            top: dot.top,
            width: dot.size,
            height: dot.size,
            animationDelay: dot.delay,
            animationDuration: `${6 + i * 0.5}s`,
          }}
        />
      ))}
    </div>
  );
}
