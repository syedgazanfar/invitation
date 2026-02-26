/**
 * Navigation Bar Component
 */
import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Box,
  Menu,
  MenuItem,
  Avatar,
  Divider,
  ListItemIcon,
  useScrollTrigger,
  Slide,
} from '@mui/material';
import {
  Menu as MenuIcon,
  AccountCircle,
  Dashboard,
  CardGiftcard,
  Logout,
  AdminPanelSettings,
} from '@mui/icons-material';
import { useAuthStore } from '../../store/authStore';

// Hide on scroll
function HideOnScroll(props: { children: React.ReactElement }) {
  const { children } = props;
  const trigger = useScrollTrigger();
  return (
    <Slide appear={false} direction="down" in={!trigger}>
      {children}
    </Slide>
  );
}

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, user, logout } = useAuthStore();
  
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [mobileMenuAnchor, setMobileMenuAnchor] = useState<null | HTMLElement>(null);

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setMobileMenuAnchor(null);
  };

  const handleLogout = async () => {
    handleMenuClose();
    await logout();
    navigate('/');
  };

  const isActive = (path: string) => location.pathname === path;

  const navLinks = [
    { label: 'Home', path: '/' },
    { label: 'Plans', path: '/plans' },
    { label: 'Templates', path: '/templates' },
  ];

  return (
    <HideOnScroll>
      <AppBar 
        position="sticky" 
        color="default" 
        elevation={0}
        sx={{ 
          bgcolor: 'background.paper',
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Toolbar sx={{ justifyContent: 'space-between' }}>
          {/* Logo */}
          <Typography
            variant="h5"
            component={Link}
            to="/"
            sx={{
              textDecoration: 'none',
              color: 'primary.main',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: 1,
            }}
          >
            <CardGiftcard fontSize="large" />
            InviteMe
          </Typography>

          {/* Desktop Navigation */}
          <Box sx={{ display: { xs: 'none', md: 'flex' }, gap: 1 }}>
            {navLinks.map((link) => (
              <Button
                key={link.path}
                component={Link}
                to={link.path}
                color={isActive(link.path) ? 'primary' : 'inherit'}
                sx={{
                  fontWeight: isActive(link.path) ? 600 : 500,
                  position: 'relative',
                  '&::after': isActive(link.path) ? {
                    content: '""',
                    position: 'absolute',
                    bottom: 0,
                    left: '20%',
                    width: '60%',
                    height: '2px',
                    bgcolor: 'primary.main',
                  } : {},
                }}
              >
                {link.label}
              </Button>
            ))}
          </Box>

          {/* Auth Buttons */}
          <Box sx={{ display: { xs: 'none', md: 'flex' }, alignItems: 'center', gap: 2 }}>
            {isAuthenticated ? (
              <>
                <IconButton
                  onClick={handleProfileMenuOpen}
                  size="small"
                  sx={{ ml: 2 }}
                >
                  <Avatar sx={{ width: 40, height: 40, bgcolor: 'primary.main' }}>
                    {user?.full_name?.[0] || user?.username?.[0] || 'U'}
                  </Avatar>
                </IconButton>
                
                <Menu
                  anchorEl={anchorEl}
                  open={Boolean(anchorEl)}
                  onClose={handleMenuClose}
                  transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                  anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
                  PaperProps={{
                    sx: { minWidth: 200, mt: 1 }
                  }}
                >
                  <Box sx={{ px: 2, py: 1 }}>
                    <Typography variant="subtitle1" fontWeight={600}>
                      {user?.full_name || user?.username}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {user?.phone}
                    </Typography>
                  </Box>
                  
                  <Divider />
                  
                  <MenuItem component={Link} to="/dashboard" onClick={handleMenuClose}>
                    <ListItemIcon>
                      <Dashboard fontSize="small" />
                    </ListItemIcon>
                    Dashboard
                  </MenuItem>
                  
                  {user?.is_staff && (
                    <MenuItem component={Link} to="/admin" onClick={handleMenuClose}>
                      <ListItemIcon>
                        <AdminPanelSettings fontSize="small" />
                      </ListItemIcon>
                      Admin Panel
                    </MenuItem>
                  )}
                  
                  <Divider />
                  
                  <MenuItem onClick={handleLogout}>
                    <ListItemIcon>
                      <Logout fontSize="small" color="error" />
                    </ListItemIcon>
                    <Typography color="error">Logout</Typography>
                  </MenuItem>
                </Menu>
              </>
            ) : (
              <>
                <Button
                  component={Link}
                  to="/login"
                  color="inherit"
                  sx={{ fontWeight: 500 }}
                >
                  Login
                </Button>
                <Button
                  component={Link}
                  to="/register"
                  variant="contained"
                  sx={{ fontWeight: 600 }}
                >
                  Get Started
                </Button>
              </>
            )}
          </Box>

          {/* Mobile Menu Button */}
          <IconButton
            sx={{ display: { xs: 'flex', md: 'none' } }}
            onClick={(e) => setMobileMenuAnchor(e.currentTarget)}
          >
            <MenuIcon />
          </IconButton>
        </Toolbar>

        {/* Mobile Menu */}
        <Menu
          anchorEl={mobileMenuAnchor}
          open={Boolean(mobileMenuAnchor)}
          onClose={handleMenuClose}
          PaperProps={{ sx: { width: '80%', maxWidth: 300 } }}
        >
          {navLinks.map((link) => (
            <MenuItem
              key={link.path}
              component={Link}
              to={link.path}
              onClick={handleMenuClose}
              selected={isActive(link.path)}
            >
              {link.label}
            </MenuItem>
          ))}
          
          <Divider />
          
          {isAuthenticated ? (
            <>
              <MenuItem component={Link} to="/dashboard" onClick={handleMenuClose}>
                <ListItemIcon><Dashboard fontSize="small" /></ListItemIcon>
                Dashboard
              </MenuItem>
              <MenuItem onClick={handleLogout}>
                <ListItemIcon><Logout fontSize="small" color="error" /></ListItemIcon>
                <Typography color="error">Logout</Typography>
              </MenuItem>
            </>
          ) : (
            <>
              <MenuItem component={Link} to="/login" onClick={handleMenuClose}>
                Login
              </MenuItem>
              <MenuItem component={Link} to="/register" onClick={handleMenuClose}>
                Get Started
              </MenuItem>
            </>
          )}
        </Menu>
      </AppBar>
    </HideOnScroll>
  );
};

export default Navbar;
