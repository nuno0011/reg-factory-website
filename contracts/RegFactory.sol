// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

interface IERC20 {
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
    function decimals() external view returns (uint8);
}

/**
 * @title RegFactory
 * @notice ERC-721 mint contract — pay USDT, get an NFT + account delivery
 */
contract RegFactory is ERC721Enumerable, Ownable, ReentrancyGuard {
    // ── State ──
    IERC20 public usdt;
    uint256 public price;              // price per mint in USDT (6 decimals)
    uint256 public maxSupply;
    uint256 public maxPerWallet;
    uint256 public totalMinted;

    string public baseURI;
    bool public mintActive;

    // USDT on Ethereum mainnet
    address constant USDT_MAINNET = 0xdAC17F958D2ee523a2206206994597C13D831ec7;

    // ── Events ──
    event AccountMinted(
        address indexed user,
        uint256 indexed tokenId,
        uint256 quantity,
        uint256 totalPaid,
        uint256 timestamp
    );

    // ── Constructor ──
    constructor(
        uint256 _price,
        uint256 _maxSupply,
        uint256 _maxPerWallet
    ) ERC721("Reg Factory", "RFCT") Ownable(msg.sender) {
        usdt = IERC20(USDT_MAINNET);
        price = _price;           // e.g. 8 USDT = 8000000 (6 decimals)
        maxSupply = _maxSupply;   // e.g. 1000
        maxPerWallet = _maxPerWallet; // e.g. 10
        mintActive = true;
    }

    // ── Mint ──
    function mint(uint256 _quantity) external nonReentrant {
        require(mintActive, "Mint not active");
        require(_quantity > 0, "Quantity must be > 0");
        require(totalMinted + _quantity <= maxSupply, "Exceeds max supply");
        require(balanceOf(msg.sender) + _quantity <= maxPerWallet, "Exceeds wallet max");

        uint256 totalCost = price * _quantity;

        // Transfer USDT from user to contract
        require(
            usdt.transferFrom(msg.sender, address(this), totalCost),
            "USDT transfer failed"
        );

        for (uint256 i = 0; i < _quantity; i++) {
            totalMinted++;
            _safeMint(msg.sender, totalMinted);
        }

        emit AccountMinted(msg.sender, totalMinted, _quantity, totalCost, block.timestamp);
    }

    // ── Owner: withdraw USDT ──
    function withdrawUSDT(address _to) external onlyOwner {
        uint256 balance = usdt.balanceOf(address(this));
        require(balance > 0, "No USDT to withdraw");
        require(usdt.transfer(_to, balance), "Transfer failed");
    }

    // ── Owner: toggle mint ──
    function toggleMint() external onlyOwner {
        mintActive = !mintActive;
    }

    // ── Owner: set price ──
    function setPrice(uint256 _price) external onlyOwner {
        price = _price;
    }

    // ── Token URI ──
    function _baseURI() internal view override returns (string memory) {
        return baseURI;
    }

    function setBaseURI(string memory _uri) external onlyOwner {
        baseURI = _uri;
    }
}
