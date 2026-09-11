function Header({
  title,
  subtitle,
}) {
  return (
    <div className="page-header">

      <div>

        <h1>
          {title}
        </h1>

        {subtitle && (
          <p>
            {subtitle}
          </p>
        )}

      </div>

    </div>
  );
}


export default Header;