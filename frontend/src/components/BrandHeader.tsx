const buuLogo = "/logos/buu_logo.png";
const instituteLogo = "/logos/buu_muh_logo.png";

interface BrandHeaderProps {
  compact?: boolean;
}

export default function BrandHeader({ compact = false }: BrandHeaderProps) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "1.5rem",
        width: "100%",
        textAlign: "center",
      }}
    >
      <img src={buuLogo} alt="BUU" width={compact ? 36 : 56} height={compact ? 36 : 56} />
      <p
        style={{
          fontSize: compact ? "1rem" : "1.2rem",
          margin: 0,
          fontWeight: 600,
          letterSpacing: 0.02,
        }}
      >
        Bursa Uludag Universitesi
      </p>
      <img src={instituteLogo} alt="Enstitu" width={compact ? 36 : 56} height={compact ? 36 : 56} />
    </div>
  );
}
