import { useId, useState } from "react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  IconButton,
  InputAdornment,
  TextField,
  Typography,
} from "@mui/material";
import VisibilityOffOutlined from "@mui/icons-material/VisibilityOffOutlined";
import VisibilityOutlined from "@mui/icons-material/VisibilityOutlined";

import { login } from "../api";

const supportedRoles = [
  "Super Admin",
  "Manager",
  "Recruiter",
  "Bench Sales Marketer",
];

export default function LoginPage({ onLogin }) {
  const waveId = useId();
  const ribbonFillId = `${waveId}-fill`;
  const ribbonEdgeId = `${waveId}-edge`;
  const ribbonBlurId = `${waveId}-blur`;

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    if (busy) return;

    setError("");
    setBusy(true);

    try {
      const result = await login(email.trim(), password);

      if (!result?.access_token || !Array.isArray(result.user?.roles)) {
        throw new Error("The server returned an unexpected login response.");
      }

      const role = supportedRoles.find((name) =>
        result.user.roles.includes(name)
      );

      if (!role) {
        throw new Error("Your account does not have access to this workspace.");
      }

      setPassword("");
      onLogin({
        token: result.access_token,
        user: result.user,
        role,
      });
    } catch (err) {
      setError(err.message || "Unable to sign in. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Box className="wave-login">
      <div className="ambient-glow" aria-hidden="true" />

      <svg
        className="wave-art"
        viewBox="0 0 1440 900"
        preserveAspectRatio="xMidYMid slice"
        aria-hidden="true"
        focusable="false"
      >
        <defs>
          <linearGradient id={ribbonFillId} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#e6edff" stopOpacity="0.2" />
            <stop offset="38%" stopColor="#bcb6ff" stopOpacity="0.65" />
            <stop offset="65%" stopColor="#6376f2" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#a7eaff" stopOpacity="0.4" />
          </linearGradient>

          <linearGradient id={ribbonEdgeId} x1="0" x2="1">
            <stop offset="0%" stopColor="#fff" stopOpacity="0.1" />
            <stop offset="45%" stopColor="#fff" stopOpacity="0.95" />
            <stop offset="100%" stopColor="#fff" stopOpacity="0.1" />
          </linearGradient>

          <filter
            id={ribbonBlurId}
            x="-20%"
            y="-30%"
            width="140%"
            height="160%"
          >
            <feGaussianBlur stdDeviation="20" />
          </filter>
        </defs>

        <path
          d="M-180 660 C180 810 380 570 680 475
             C980 380 1160 540 1620 350 L1620 610
             C1200 760 1020 540 710 635
             C390 735 140 950 -180 820 Z"
          fill={`url(#${ribbonFillId})`}
          filter={`url(#${ribbonBlurId})`}
        />

        <path
          d="M-140 650 C180 790 380 555 680 475
             C990 390 1180 550 1600 350"
          fill="none"
          stroke={`url(#${ribbonEdgeId})`}
          strokeWidth="5"
        />

        <path
          d="M-140 700 C180 840 390 610 700 520
             C1000 435 1190 600 1600 405"
          fill="none"
          stroke="#fff"
          strokeOpacity="0.23"
          strokeWidth="2"
        />

        <path
          d="M-140 745 C180 870 390 655 700 565
             C1000 480 1190 650 1600 450"
          fill="none"
          stroke="#d6e9ff"
          strokeOpacity="0.45"
          strokeWidth="2"
        />
      </svg>

      <Box className="wave-login-layout">

        <Box
          component="main"
          className="glass-login-card"
          sx={{
            gridColumn: "2",
            "@media (max-width: 760px)": { gridColumn: "1" },
          }}
        >
          <Typography component="h1" id="login-title" className="login-title">
            Sign in
          </Typography>

          <Box
            component="form"
            onSubmit={handleSubmit}
            aria-labelledby="login-title"
            aria-busy={busy}
            sx={{ mt: 3 }}
          >
            {error && (
              <Alert severity="error" sx={{ mb: 2.5 }}>
                {error}
              </Alert>
            )}

            <Box className="login-field">
              <label htmlFor="login-email">Work email</label>
              <TextField
                id="login-email"
                name="email"
                className="glass-input"
                type="email"
                autoComplete="username"
                required
                fullWidth
                disabled={busy}
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </Box>

            <Box className="login-field">
              <label htmlFor="login-password">Password</label>
              <TextField
                id="login-password"
                name="password"
                className="glass-input"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                required
                fullWidth
                disabled={busy}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          type="button"
                          edge="end"
                          disabled={busy}
                          aria-label={showPassword ? "Hide password" : "Show password"}
                          onClick={() => setShowPassword((visible) => !visible)}
                        >
                          {showPassword ? (
                            <VisibilityOffOutlined fontSize="small" />
                          ) : (
                            <VisibilityOutlined fontSize="small" />
                          )}
                        </IconButton>
                      </InputAdornment>
                    ),
                  },
                }}
              />
            </Box>

            <Button
              className="gradient-login-button"
              type="submit"
              variant="contained"
              fullWidth
              disabled={busy}
            >
              {busy && (
                <CircularProgress size={18} color="inherit" sx={{ mr: 1.5 }} />
              )}
              {busy ? "Signing in…" : "Sign in"}
            </Button>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}