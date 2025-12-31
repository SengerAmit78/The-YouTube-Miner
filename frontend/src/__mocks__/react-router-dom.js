module.exports = {
  useNavigate: () => jest.fn(),
  useLocation: () => ({}),
  useParams: () => ({}),
  BrowserRouter: ({ children }) => children,
  Route: ({ children }) => children,
  Routes: ({ children }) => children,
  Navigate: () => null,
};
